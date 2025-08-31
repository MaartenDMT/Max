import asyncio
from typing import Annotated, Literal, Optional

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

try:  # langgraph is optional — degrade gracefully if unavailable
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.graph import CompiledGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode
    _LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    END = None
    START = None
    StateGraph = None
    CompiledGraph = None
    add_messages = lambda x: x
    ToolNode = None
    _LANGGRAPH_AVAILABLE = False
from pydantic import BaseModel, Field

from ai_tools.lc_tools import (music_generate, research, video_summarize,
                               web_research, website_summarize)
from utils.loggers import LoggerSetup


class AgentState(BaseModel):
    """Graph state: conversational messages, optional final_response, and router decision."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    final_response: Optional[str] = None
    route: Optional[Literal["tools", "respond", "crew", "end"]] = None


class OrchestratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        # Bind tools for the agent model
        self.tools = [
            website_summarize,
            web_research,
            research,
            video_summarize,
            music_generate,
        ]
        self.model_with_tools = self.llm.bind_tools(self.tools)

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "OrchestratorAgent", "orchestrator_agent.log"
        )
        self.logger.info("OrchestratorAgent initialized.")

        self.graph = self._build_graph()

    def _call_model(self, state: AgentState) -> dict:
        """Call the model; returns dict update for messages list."""
        response = self.model_with_tools.invoke(state.messages)
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> Literal["tools", "respond"]:
        last = state.messages[-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return "respond"

    def _respond(self, state: AgentState) -> dict:
        """Compose the final response. If last step was a tool call, summarize its result."""
        msgs = state.messages
        # If tool used, last two messages are AI (with tool call) then ToolMessage
        content = None
        if msgs and msgs[-1].type == "tool":
            content = msgs[-1].content
        else:
            # No tool last step: ask the base model to respond succinctly.
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "You are a concise helpful assistant."),
                    ("human", "{input}"),
                ]
            )
            chain = prompt | self.llm
            human_last = next((m for m in reversed(msgs) if m.type == "human"), None)
            text = human_last.content if human_last else ""
            resp = chain.invoke({"input": text})
            content = resp.content
        return {"final_response": str(content), "route": "end"}

    def _build_graph(self) -> CompiledGraph:
        if not _LANGGRAPH_AVAILABLE:  # pragma: no cover - runtime fallback
            self.logger.warning(
                "langgraph not installed; orchestrator graph disabled — using fallback flow."
            )
            return None

        workflow = StateGraph(AgentState)

        # Nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("respond", self._respond)

        # Edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent", self._should_continue, {"tools": "tools", "respond": "respond"}
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("respond", END)

        return workflow.compile()

    async def run_workflow(self, query: str) -> str:
        """Run graph and return final response string."""
        initial = AgentState(messages=[HumanMessage(content=query)])
        final = None
        # If langgraph unavailable, run a simplified single-step flow: call model then respond.
        if not _LANGGRAPH_AVAILABLE or self.graph is None:  # pragma: no cover - fallback path
            try:
                update = self._call_model(initial)
                # model returns {'messages': [response]}
                msgs = initial.messages + update.get("messages", [])
                state = AgentState(messages=msgs)
                resp = self._respond(state)
                return resp.get("final_response") or "No response generated."
            except Exception:
                self.logger.exception("Orchestrator fallback failed.")
                return "Orchestrator unavailable."

        async for update in self.graph.astream(initial):
            if "__end__" in update:
                final = update["__end__"].get("final_response")
        return final or "No response generated."


if __name__ == "__main__":

    async def test_orchestrator():
        orchestrator = OrchestratorAgent()
        print("\n--- Testing simple query ---")
        response = await orchestrator.run_workflow("Summarize https://example.com for the question: what is this site about?")
        print(f"Final Response: {response}")

        print("\n--- Testing complex query with CrewAI ---")
        response = await orchestrator.run_workflow(
            "Please research recent AI trends and write a concise summary."
        )
        print(f"Final Response: {response}")

    asyncio.run(test_orchestrator())
    asyncio.run(test_orchestrator())
