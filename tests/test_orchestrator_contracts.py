from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from agents.enhanced_orchestrator_agent import (EnhancedAgentState,
                                                EnhancedOrchestratorAgent)
from api.schemas import OrchestratorRunWorkflowRequest


@pytest.mark.asyncio
@patch('agents.enhanced_orchestrator_agent.ChatOpenAI')
async def test_graph_nodes_return_dicts(MockChatOpenAI):
    # Mock model to avoid network calls
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.ainvoke = MagicMock(return_value=AIMessage(content="ok"))
    MockChatOpenAI.return_value = mock_llm

    orch = EnhancedOrchestratorAgent(enable_memory=False)
    state = EnhancedAgentState(messages=[HumanMessage(content="do research on ai")])
    state.current_task_type = "analysis"

    # Call async node directly and ensure dict is returned
    out = await orch._run_crew_collaboration(state)
    assert isinstance(out, dict)
    assert 'messages' in out or 'route' in out


@pytest.mark.asyncio
@patch('agents.enhanced_orchestrator_agent.ChatOpenAI')
async def test_run_workflow_contracts(MockChatOpenAI):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.ainvoke = MagicMock(return_value=AIMessage(content="ok"))
    MockChatOpenAI.return_value = mock_llm

    orch = EnhancedOrchestratorAgent(enable_memory=False)

    # Legacy style returns a string
    legacy = await orch.run_workflow("hello", "s1")
    assert isinstance(legacy, str)

    # New request returns structured response
    req = OrchestratorRunWorkflowRequest(query="hello", session_id="s2")
    resp = await orch.run_workflow(req)
    assert hasattr(resp, 'status') and hasattr(resp, 'final_response')
