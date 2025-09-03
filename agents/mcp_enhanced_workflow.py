import asyncio
from typing import Annotated, Literal, Optional, Dict, Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from api.schemas import OrchestratorRunWorkflowRequest, OrchestratorRunWorkflowResponse
from utils.llm_manager import LLMManager, LLMConfig
from decouple import config as decouple_config

# Import system assistant for MCP-enhanced tools
from assistents.system_assistent import SystemAssistant

llm_config_data = {
    "llm_provider": decouple_config("LLM_PROVIDER", default="ollama"),
    "anthropic_api_key": decouple_config("ANTHROPIC_API_KEY", default=None),
    "openai_api_key": decouple_config("OPENAI_API_KEY", default=None),
    "openrouter_api_key": decouple_config("OPENROUTER_API_KEY", default=None),
    "gemini_api_key": decouple_config("GEMINI_API_KEY", default=None),
}
llm_manager = LLMManager(LLMConfig(**llm_config_data))

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


class MCPEnhancedAgentState(BaseModel):
    """Enhanced graph state with MCP context capabilities."""
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    final_response: Optional[str] = None
    route: Optional[Literal["tools", "respond", "mcp_enhanced", "end"]] = None
    mcp_context: Optional[Dict[str, Any]] = None  # Store MCP-enhanced context data


class MCPEnhancedOrchestratorAgent:
    """Orchestrator agent with enhanced MCP capabilities."""

    def __init__(self):
        # Initialize LLM
        self.llm = llm_manager.get_llm()
        
        # Initialize system assistant for MCP-enhanced tools
        self.system_assistant = SystemAssistant(None, None, None)
        
        # Define tools with MCP-enhanced capabilities
        self.tools = [
            music_generate,
            research,
            video_summarize,
            web_research,
            website_summarize,
            self._get_system_info_mcp,
            self._get_network_info_mcp,
            self._get_process_list_mcp,
            self._search_processes_mcp,
            self._get_battery_info_mcp,
        ]
        
        # Setup logger
        from utils.loggers import LoggerSetup
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("MCPEnhancedOrchestrator", "mcp_orchestrator.log")
        self.logger.info("MCP Enhanced Orchestrator initialized.")

    def _get_system_info_mcp(self, query: str = ""):
        """Get comprehensive system information using MCP-enhanced approach."""
        return asyncio.run(self.system_assistant._get_system_info_api())

    def _get_network_info_mcp(self, query: str = ""):
        """Get network information using MCP-enhanced approach."""
        return asyncio.run(self.system_assistant._get_network_info_api())

    def _get_process_list_mcp(self, query: str = ""):
        """Get list of running processes using MCP-enhanced approach."""
        return asyncio.run(self.system_assistant._get_process_list_api())

    def _search_processes_mcp(self, query: str):
        """Search for specific processes using MCP-enhanced approach."""
        return asyncio.run(self.system_assistant._search_processes_api(query))

    def _get_battery_info_mcp(self, query: str = ""):
        """Get detailed battery information using MCP-enhanced approach."""
        return asyncio.run(self.system_assistant._get_battery_info_api())

    def _call_model(self, state: MCPEnhancedAgentState):
        """Call the language model with enhanced MCP context."""
        system_message = """
        You are an advanced AI assistant with access to enhanced system tools via the Model Context Protocol (MCP).
        You can gather detailed system information, network data, process lists, and battery status.
        Use these tools when appropriate to provide comprehensive responses about the system state.
        
        When responding to user queries, you can:
        1. Gather system information using available MCP-enhanced tools
        2. Analyze the data and provide meaningful insights
        3. Help with troubleshooting system issues
        4. Monitor system performance and resource usage
        
        Current MCP context: {mcp_context}
        """.format(mcp_context=state.mcp_context or "No context available")
        
        response = self.llm.invoke([
            HumanMessage(content=system_message),
            *state.messages
        ])
        
        return {"messages": [response]}

    def _should_continue(self, state: MCPEnhancedAgentState) -> Literal["tools", "mcp_enhanced", "respond", "end"]:
        """Determine the next step in the workflow based on the model's response."""
        last_message = state.messages[-1]
        
        # Check if the model wants to use tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
            
        # Check if the model wants to use MCP-enhanced capabilities
        content = last_message.content.lower() if hasattr(last_message, 'content') else ""
        if any(keyword in content for keyword in ["system info", "network info", "process list", "battery info", "search process"]):
            return "mcp_enhanced"
            
        # Check if we have a final response
        if state.final_response:
            return "end"
            
        return "respond"

    def _run_mcp_enhanced(self, state: MCPEnhancedAgentState):
        """Run MCP-enhanced operations based on the request."""
        last_message = state.messages[-1]
        content = last_message.content if hasattr(last_message, 'content') else ""
        
        # Determine which MCP-enhanced operation to perform
        mcp_context = {}
        
        if "system info" in content.lower():
            result = asyncio.run(self.system_assistant._get_system_info_api())
            mcp_context["system_info"] = result
        elif "network info" in content.lower():
            result = asyncio.run(self.system_assistant._get_network_info_api())
            mcp_context["network_info"] = result
        elif "process list" in content.lower():
            result = asyncio.run(self.system_assistant._get_process_list_api())
            mcp_context["process_list"] = result
        elif "battery info" in content.lower():
            result = asyncio.run(self.system_assistant._get_battery_info_api())
            mcp_context["battery_info"] = result
        elif "search process" in content.lower():
            # Extract search term
            search_term = content.lower().replace("search process", "").strip()
            if search_term:
                result = asyncio.run(self.system_assistant._search_processes_api(search_term))
                mcp_context["process_search"] = result
            else:
                mcp_context["error"] = "No search term provided"
        
        return {"mcp_context": mcp_context}

    def _respond(self, state: MCPEnhancedAgentState):
        """Generate the final response based on all gathered information."""
        # Combine the messages and MCP context for the final response
        context_info = f"\n\nMCP Context: {state.mcp_context}" if state.mcp_context else ""
        
        response_content = state.messages[-1].content + context_info if state.messages else "No response generated."
        
        return {"final_response": response_content}

    def _create_workflow(self) -> CompiledGraph:
        """Create the enhanced workflow graph with MCP capabilities."""
        if not _LANGGRAPH_AVAILABLE:
            raise RuntimeError("langgraph is required for workflow functionality")
            
        workflow = StateGraph(MCPEnhancedAgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("mcp_enhanced", self._run_mcp_enhanced)
        workflow.add_node("respond", self._respond)

        # Add edges
        workflow.add_edge(START, "agent")

        # Enhanced conditional routing with MCP capabilities
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "mcp_enhanced": "mcp_enhanced",
                "respond": "respond",
                "end": END
            }
        )

        workflow.add_edge("tools", "agent")
        workflow.add_edge("mcp_enhanced", "agent")
        workflow.add_edge("respond", END)

        # Compile the workflow
        return workflow.compile()

    async def run_workflow(self, request: OrchestratorRunWorkflowRequest) -> OrchestratorRunWorkflowResponse:
        """Run enhanced workflow with MCP capabilities."""
        try:
            # Create the workflow
            workflow = self._create_workflow()
            
            # Initialize the state
            initial_state = MCPEnhancedAgentState(
                messages=[HumanMessage(content=request.query)]
            )
            
            # Run the workflow
            final_state = workflow.invoke(initial_state)
            
            # Extract the final response
            final_response_content = final_state.final_response or "Workflow completed without final response."
            
            return OrchestratorRunWorkflowResponse(
                status="success",
                final_response=final_response_content,
                session_id=request.session_id
            )
            
        except Exception as e:
            self.logger.exception(f"Enhanced workflow execution failed: {str(e)}")
            return OrchestratorRunWorkflowResponse(
                status="error",
                message=f"I encountered an error: {str(e)}. Please try again.",
                final_response=f"I encountered an error: {str(e)}. Please try again.",
                session_id=request.session_id
            )