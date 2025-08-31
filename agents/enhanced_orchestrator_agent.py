"""
Enhanced Orchestrator Agent with LangGraph Memory Management and CrewAI Best Practices
"""
import asyncio
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

try:
    from langgraph.checkpoint.base import CheckpointSaver
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.graph import CompiledGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode
    _LANGGRAPH_AVAILABLE = True
except Exception:
    END = None
    START = None
    StateGraph = None
    CompiledGraph = None
    add_messages = lambda x: x
    ToolNode = None
    MemorySaver = None
    CheckpointSaver = None
    _LANGGRAPH_AVAILABLE = False

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from ai_tools.lc_tools import (
    music_generate,
    research,
    video_summarize,
    web_research,
    website_summarize,
)
from utils.loggers import LoggerSetup


class ConversationContext(BaseModel):
    """Structured conversation context with memory"""
    session_id: str
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_topics: List[str] = Field(default_factory=list)
    agent_memory: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EnhancedAgentState(BaseModel):
    """Enhanced state with memory management and structured data"""

    # Core conversation state
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)

    # Context and memory
    conversation_context: ConversationContext = Field(default_factory=lambda: ConversationContext(session_id="default"))

    # Routing and workflow
    route: Optional[Literal["tools", "respond", "crew", "analysis", "end"]] = None
    final_response: Optional[str] = None

    # Task execution state
    current_task_type: Optional[str] = None
    task_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Memory and learning
    key_insights: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)

    # Error handling and retry
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None


class EnhancedOrchestratorAgent:
    """
    Enhanced Orchestrator Agent with:
    - LangGraph memory management and checkpointing
    - CrewAI collaboration patterns
    - Structured state management
    - Enhanced error handling
    """

    def __init__(self, enable_memory: bool = True):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Enhanced tools with better organization
        self.tools = [
            website_summarize,
            web_research,
            research,
            video_summarize,
            music_generate,
        ]
        self.model_with_tools = self.llm.bind_tools(self.tools)

        # Memory management
        self.enable_memory = enable_memory
        self.checkpointer = MemorySaver() if _LANGGRAPH_AVAILABLE and enable_memory else None

        # CrewAI agents for collaboration
        self._initialize_crew_agents()

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("EnhancedOrchestratorAgent", "enhanced_orchestrator.log")
        self.logger.info("Enhanced OrchestratorAgent initialized with memory management.")

        # Build enhanced graph
        self.graph = self._build_enhanced_graph()

    def _initialize_crew_agents(self):
        """Initialize CrewAI agents with memory enabled"""

        self.researcher_agent = Agent(
            role="Research Specialist",
            goal="Conduct comprehensive research and provide detailed analysis",
            backstory="""You are an expert researcher with deep analytical skills.
            You excel at finding reliable sources, fact-checking information,
            and providing comprehensive analysis across various domains.""",
            memory=True,  # Enable CrewAI memory
            allow_delegation=True,
            verbose=True
        )

        self.analyst_agent = Agent(
            role="Data Analyst",
            goal="Analyze patterns, extract insights, and provide data-driven recommendations",
            backstory="""You are a skilled data analyst who excels at identifying patterns,
            extracting meaningful insights from complex information, and providing
            actionable recommendations based on data analysis.""",
            memory=True,  # Enable CrewAI memory
            allow_delegation=True,
            verbose=True
        )

        self.content_agent = Agent(
            role="Content Strategist",
            goal="Transform research and analysis into engaging, structured content",
            backstory="""You are an experienced content strategist who excels at
            transforming complex research and analysis into clear, engaging content
            that resonates with the target audience.""",
            memory=True,  # Enable CrewAI memory
            allow_delegation=True,
            verbose=True
        )

    def _call_model(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Enhanced model calling with context awareness"""

        # Extract conversation context for better prompting
        context = state.conversation_context
        recent_topics = ", ".join(context.last_topics[-3:]) if context.last_topics else "None"

        # Enhanced system message with context
        system_context = f"""You are an intelligent AI assistant with access to various tools.

        Conversation Context:
        - Session ID: {context.session_id}
        - Recent topics: {recent_topics}
        - Total messages in conversation: {len(state.messages)}

        Use this context to provide more relevant and personalized responses.
        """

        # Add system context to messages if not present
        messages = state.messages.copy()
        if not messages or messages[0].type != "system":
            messages.insert(0, AIMessage(content=system_context))

        try:
            response = self.model_with_tools.invoke(messages)

            # Update conversation context
            self._update_conversation_context(state, response)

            return {"messages": [response]}

        except Exception as e:
            self.logger.error(f"Model call failed: {str(e)}")
            state.retry_count += 1
            state.last_error = str(e)

            if state.retry_count <= state.max_retries:
                self.logger.info(f"Retrying model call ({state.retry_count}/{state.max_retries})")
                return self._call_model(state)
            else:
                # Fallback response
                fallback_msg = AIMessage(content="I apologize, but I'm having technical difficulties. Please try again.")
                return {"messages": [fallback_msg]}

    def _update_conversation_context(self, state: EnhancedAgentState, response: BaseMessage):
        """Update conversation context with new insights"""

        context = state.conversation_context
        context.updated_at = datetime.now()

        # Extract topics from the response (simple keyword extraction)
        content = response.content.lower() if hasattr(response, 'content') else ""

        # Add to conversation history
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "ai_response",
            "content": content[:200] + "..." if len(content) > 200 else content
        })

        # Keep history manageable
        if len(context.conversation_history) > 50:
            context.conversation_history = context.conversation_history[-30:]

    def _should_continue(self, state: EnhancedAgentState) -> Literal["tools", "crew", "analysis", "respond"]:
        """Enhanced routing logic with crew collaboration"""

        last_message = state.messages[-1] if state.messages else None

        if not last_message:
            return "respond"

        # Check for tool calls first
        if getattr(last_message, "tool_calls", None):
            return "tools"

        # Analyze content for complex research/analysis needs
        content = last_message.content.lower() if hasattr(last_message, 'content') else ""

        research_keywords = ["research", "analyze", "investigate", "study", "explore", "examine"]
        analysis_keywords = ["analysis", "pattern", "insight", "recommendation", "strategy"]

        if any(keyword in content for keyword in research_keywords):
            state.current_task_type = "research"
            return "crew"
        elif any(keyword in content for keyword in analysis_keywords):
            state.current_task_type = "analysis"
            return "analysis"

        return "respond"

    def _run_crew_collaboration(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Run CrewAI collaboration based on task type"""

        try:
            last_message = state.messages[-1] if state.messages else None
            user_request = last_message.content if last_message and hasattr(last_message, 'content') else ""

            if state.current_task_type == "research":
                return self._execute_research_crew(user_request, state)
            else:
                return self._execute_analysis_crew(user_request, state)

        except Exception as e:
            self.logger.error(f"Crew collaboration failed: {str(e)}")
            error_msg = AIMessage(content=f"I encountered an issue during collaboration: {str(e)}")
            return {"messages": [error_msg], "route": "respond"}

    def _execute_research_crew(self, user_request: str, state: EnhancedAgentState) -> Dict[str, Any]:
        """Execute research-focused crew collaboration"""

        # Create research task
        research_task = Task(
            description=f"""Conduct comprehensive research on: {user_request}

            Provide:
            1. Key findings and insights
            2. Relevant data and statistics
            3. Multiple perspectives on the topic
            4. Reliable sources and references

            Focus on accuracy and depth of analysis.""",
            expected_output="Comprehensive research report with key findings, data, and sources",
            agent=self.researcher_agent
        )

        # Create analysis task that builds on research
        analysis_task = Task(
            description=f"""Analyze the research findings and provide strategic insights for: {user_request}

            Based on the research, provide:
            1. Pattern analysis and trends
            2. Strategic recommendations
            3. Potential implications
            4. Actionable next steps""",
            expected_output="Strategic analysis with recommendations and actionable insights",
            agent=self.analyst_agent,
            context=[research_task]  # Uses research output as context
        )

        # Create crew with sequential process
        research_crew = Crew(
            agents=[self.researcher_agent, self.analyst_agent],
            tasks=[research_task, analysis_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute crew
        result = research_crew.kickoff()

        # Store insights in state
        state.key_insights.append(f"Research: {user_request}")
        state.topics_discussed.append(user_request)

        # Create response message
        response_msg = AIMessage(content=str(result.raw))
        return {"messages": [response_msg], "route": "respond"}

    def _execute_analysis_crew(self, user_request: str, state: EnhancedAgentState) -> Dict[str, Any]:
        """Execute analysis-focused crew collaboration"""

        # Create analysis task
        analysis_task = Task(
            description=f"""Perform detailed analysis for: {user_request}

            Provide:
            1. Data analysis and pattern identification
            2. Key insights and findings
            3. Strategic recommendations
            4. Risk assessment and opportunities""",
            expected_output="Detailed analysis report with insights and recommendations",
            agent=self.analyst_agent
        )

        # Create content strategy task
        content_task = Task(
            description=f"""Transform the analysis into actionable content strategy for: {user_request}

            Create:
            1. Clear summary of findings
            2. Prioritized recommendations
            3. Implementation roadmap
            4. Success metrics""",
            expected_output="Actionable content strategy with implementation plan",
            agent=self.content_agent,
            context=[analysis_task]
        )

        # Create crew
        analysis_crew = Crew(
            agents=[self.analyst_agent, self.content_agent],
            tasks=[analysis_task, content_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute crew
        result = analysis_crew.kickoff()

        # Store insights
        state.key_insights.append(f"Analysis: {user_request}")
        state.topics_discussed.append(user_request)

        response_msg = AIMessage(content=str(result.raw))
        return {"messages": [response_msg], "route": "respond"}

    def _respond(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Enhanced response generation with memory context"""

        msgs = state.messages
        context = state.conversation_context

        # Generate context-aware response
        if msgs and msgs[-1].type == "tool":
            # Tool result summarization
            content = msgs[-1].content
        else:
            # Generate response using conversation context
            system_prompt = f"""You are a helpful AI assistant with conversation memory.

            Conversation Context:
            - Previous topics: {', '.join(context.last_topics[-3:]) if context.last_topics else 'None'}
            - Key insights from this session: {', '.join(state.key_insights[-3:]) if state.key_insights else 'None'}
            - Session duration: {(datetime.now() - context.created_at).total_seconds() / 60:.1f} minutes

            Provide a helpful, contextual response that builds on our conversation history."""

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])

            chain = prompt | self.llm
            human_last = next((m for m in reversed(msgs) if m.type == "human"), None)
            text = human_last.content if human_last else ""

            resp = chain.invoke({"input": text})
            content = resp.content

        # Update context with final response
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "final_response",
            "content": content[:200] + "..." if len(content) > 200 else content
        })

        return {"final_response": str(content), "route": "end"}

    def _build_enhanced_graph(self) -> CompiledGraph:
        """Build enhanced StateGraph with memory and collaboration"""

        if not _LANGGRAPH_AVAILABLE:
            self.logger.warning("LangGraph not available; using fallback mode.")
            return None

        workflow = StateGraph(EnhancedAgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("crew", self._run_crew_collaboration)
        workflow.add_node("analysis", self._run_crew_collaboration)  # Same method, different routing
        workflow.add_node("respond", self._respond)

        # Add edges
        workflow.add_edge(START, "agent")

        # Enhanced conditional routing
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "crew": "crew",
                "analysis": "analysis",
                "respond": "respond"
            }
        )

        workflow.add_edge("tools", "agent")
        workflow.add_edge("crew", "respond")
        workflow.add_edge("analysis", "respond")
        workflow.add_edge("respond", END)

        # Compile with checkpointer for memory
        return workflow.compile(checkpointer=self.checkpointer)

    async def run_workflow(self, query: str, session_id: str = "default") -> str:
        """Run enhanced workflow with session management"""

        # Initialize state with session context
        context = ConversationContext(session_id=session_id)
        initial_state = EnhancedAgentState(
            messages=[HumanMessage(content=query)],
            conversation_context=context
        )

        # Fallback mode if LangGraph unavailable
        if not _LANGGRAPH_AVAILABLE or self.graph is None:
            self.logger.warning("Using fallback mode without memory")
            try:
                update = self._call_model(initial_state)
                msgs = initial_state.messages + update.get("messages", [])
                state = EnhancedAgentState(messages=msgs, conversation_context=context)
                resp = self._respond(state)
                return resp.get("final_response") or "No response generated."
            except Exception:
                self.logger.exception("Enhanced orchestrator fallback failed.")
                return "Assistant temporarily unavailable."

        # Run with memory persistence
        config = {"configurable": {"thread_id": session_id}}

        try:
            final_state = None
            async for update in self.graph.astream(initial_state, config=config):
                if "__end__" in update:
                    final_state = update["__end__"]
                    break

            if final_state and hasattr(final_state, 'final_response'):
                return final_state.final_response or "No response generated."
            else:
                return "Workflow completed without final response."

        except Exception as e:
            self.logger.exception(f"Enhanced workflow execution failed: {str(e)}")
            return f"I encountered an error: {str(e)}. Please try again."

    def get_conversation_summary(self, session_id: str = "default") -> Dict[str, Any]:
        """Get conversation summary for a session"""

        # This would typically query from persistent storage
        # For now, return basic structure
        return {
            "session_id": session_id,
            "topics_discussed": [],
            "key_insights": [],
            "conversation_length": 0,
            "last_activity": datetime.now().isoformat()
        }


# Testing and usage example
if __name__ == "__main__":
    async def test_enhanced_orchestrator():
        orchestrator = EnhancedOrchestratorAgent(enable_memory=True)

        print("\n--- Testing Enhanced Memory and Collaboration ---")

        # Test 1: Simple query
        response1 = await orchestrator.run_workflow(
            "Hello, I'm interested in learning about AI trends",
            session_id="test_session_1"
        )
        print(f"Response 1: {response1}")

        # Test 2: Research collaboration
        response2 = await orchestrator.run_workflow(
            "Please research the latest developments in quantum computing",
            session_id="test_session_1"
        )
        print(f"Response 2: {response2}")

        # Test 3: Analysis collaboration
        response3 = await orchestrator.run_workflow(
            "Analyze the impact of quantum computing on cybersecurity",
            session_id="test_session_1"
        )
        print(f"Response 3: {response3}")

        # Test conversation summary
        summary = orchestrator.get_conversation_summary("test_session_1")
        print(f"Session Summary: {summary}")

    asyncio.run(test_enhanced_orchestrator())
