import asyncio
from typing import Literal, List

from crewai import Agent, Task, Crew, Process
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field  # Updated import for Pydantic v2
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langchain_core.tools import BaseTool  # Import BaseTool for type hinting

from utils.loggers import LoggerSetup
from ai_tools.crew_tools import (
    WebsiteSummarizerTool,  # Import the tool classes
    WebPageResearcherTool,  # Import the tool classes
)


class AgentState(BaseModel):
    """Represents the state of our agent in the graph."""

    query: str = Field(description="The user's query.")
    response: str = Field(description="The agent's response.")
    tool_output: str = Field(description="The output of any tool used.")
    next_step: Literal["tool", "respond", "end", "determine_intent", "crew"] = Field(
        description="The next step for the agent."
    )


class OrchestratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.graph = self._build_graph()
        # No longer instantiate tool classes, use functions directly
        # self.website_summarizer_tool = WebsiteSummarizerTool()
        # self.web_page_researcher_tool = WebPageResearcherTool()

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "OrchestratorAgent", "orchestrator_agent.log"
        )
        self.logger.info("OrchestratorAgent initialized.")

    def _build_graph(self) -> CompiledGraph:
        """Builds the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("determine_intent", self._determine_intent)
        workflow.add_node("execute_tool", self._execute_tool)
        workflow.add_node("run_crew_task", self._run_crew_task)  # New node for CrewAI
        workflow.add_node("generate_response", self._generate_response)

        # Define edges
        workflow.set_entry_point("determine_intent")
        workflow.add_conditional_edges(
            "determine_intent",
            lambda state: state.next_step,
            {
                "tool": "execute_tool",
                "crew": "run_crew_task",  # Transition to crew_task
                "respond": "generate_response",
                "end": END,
            },
        )
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge(
            "run_crew_task", "generate_response"
        )  # After crew, generate response
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    async def _determine_intent(self, state: AgentState) -> AgentState:
        """Determines the intent of the user's query."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an intelligent assistant. Based on the user's query, "
                    "determine the next step: 'tool' if a specific tool is needed, "
                    "'respond' if a direct response can be generated, or 'end' if the task is complete.",
                ),
                ("human", "{query}"),
            ]
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"query": state.query})
        # This is a placeholder. In a real scenario, you'd parse the LLM's response
        # to determine the actual next_step and potentially which tool to use.
        # For now, we'll assume it always needs a tool for demonstration.
        response_content_str = str(response.content)  # Ensure content is string
        self.logger.info(
            f"Determined intent for query '{state.query}': {response_content_str}"
        )
        # For demonstration, let's assume if "complex" is in query, it goes to crew.
        # In a real scenario, the LLM would output a structured decision.
        if "complex" in response_content_str.lower():
            state.next_step = "crew"
        elif "tool" in response_content_str.lower():
            state.next_step = "tool"
        elif "respond" in response_content_str.lower():
            state.next_step = "respond"
        else:
            state.next_step = "end"
        return state

    async def _execute_tool(self, state: AgentState) -> AgentState:
        """Executes a tool based on the determined intent."""
        # This is a placeholder for actual tool execution.
        # In a real scenario, you would call the appropriate tool based on the intent.
        self.logger.info(f"Executing tool for query: {state.query}")
        state.tool_output = f"Tool executed for: {state.query}"
        state.next_step = "respond"  # After tool, usually generate a response
        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generates a final response to the user."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. Generate a concise response based on the query and tool output.",
                ),
                ("human", "Query: {query}\nTool Output: {tool_output}"),
            ]
        )
        chain = prompt | self.llm
        response = await chain.ainvoke(
            {"query": state.query, "tool_output": state.tool_output}
        )
        response_content_str = str(response.content)  # Ensure content is string
        self.logger.info(
            f"Generated response for query '{state.query}': {response_content_str}"
        )
        state.response = response_content_str
        state.next_step = "end"
        return state

    async def _run_crew_task(self, state: AgentState) -> AgentState:
        """Runs a CrewAI task for complex queries."""
        self.logger.info(f"Running CrewAI task for query: {state.query}")

        # Define agents
        researcher = Agent(
            role="Researcher",
            goal=f"Uncover groundbreaking information about {state.query}",
            backstory="An expert in information retrieval and data synthesis.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[WebPageResearcherTool()],  # Instantiate the tool class
        )
        writer = Agent(
            role="Writer",
            goal=f"Create a compelling and engaging response based on research",
            backstory="A skilled wordsmith, able to craft clear and compelling narratives.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[WebsiteSummarizerTool()],  # Instantiate the tool class
        )

        # Define tasks
        research_task = Task(
            description=f"Conduct a comprehensive analysis of {state.query}, identifying key trends and facts.",
            expected_output="A detailed report with bullet points summarizing the key findings.",
            agent=researcher,
        )
        write_task = Task(
            description="Write a comprehensive response based on the research findings.",
            agent=writer,
            context=[research_task],
            expected_output="A well-structured and informative response.",
        )

        # Instantiate your crew
        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, write_task],
            process=Process.sequential,  # or Process.hierarchical
            verbose=True,  # Changed from 2 to True
        )

        # Kickoff the crew
        crew_result = await asyncio.to_thread(crew.kickoff)
        self.logger.info(f"CrewAI task completed. Result: {crew_result}")
        state.tool_output = f"CrewAI processed: {state.query}. Result: {crew_result}"
        state.next_step = "respond"
        return state

    async def run_workflow(self, query: str) -> str:
        """Runs the LangGraph workflow with the given query."""
        initial_state = AgentState(
            query=query, response="", tool_output="", next_step="determine_intent"
        )
        async for state in self.graph.astream(initial_state):
            self.logger.info(f"Current state: {state}")
            if "__end__" in state:
                final_state = state["__end__"]
                return final_state["response"]
        return "No response generated."


if __name__ == "__main__":

    async def test_orchestrator():
        orchestrator = OrchestratorAgent()
        print("\n--- Testing simple query ---")
        response = await orchestrator.run_workflow("What is the weather like today?")
        print(f"Final Response: {response}")

        print("\n--- Testing complex query with CrewAI ---")
        response = await orchestrator.run_workflow(
            "Explain the concept of quantum entanglement in simple terms."
        )
        print(f"Final Response: {response}")

    asyncio.run(test_orchestrator())
