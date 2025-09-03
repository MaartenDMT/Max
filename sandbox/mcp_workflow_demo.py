#!/usr/bin/env python3
"""
MCP-Enhanced Workflow Demo

This script demonstrates the new workflow patterns leveraging Context7 MCP capabilities
that have been added to the system assistant.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.mcp_enhanced_workflow import MCPEnhancedOrchestratorAgent
from api.schemas import OrchestratorRunWorkflowRequest


async def demo_mcp_workflow():
    """Demonstrate the MCP-enhanced workflow capabilities."""
    print("=== MCP-Enhanced Workflow Demo ===\n")
    
    # Initialize the MCP-enhanced orchestrator
    orchestrator = MCPEnhancedOrchestratorAgent()
    
    # Test cases for different MCP-enhanced capabilities
    test_cases = [
        "Get comprehensive system information",
        "Show me the current network configuration",
        "List all running processes",
        "Search for processes containing 'python'",
        "Get detailed battery information"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"{i}. Testing: {query}")
        
        # Create a workflow request
        request = OrchestratorRunWorkflowRequest(
            query=query,
            session_id=f"demo_session_{i}"
        )
        
        # Run the workflow
        try:
            response = await orchestrator.run_workflow(request)
            print(f"   Status: {response.status}")
            print(f"   Response: {response.final_response[:200]}..." if len(response.final_response) > 200 else f"   Response: {response.final_response}")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        print()


def main():
    """Main function to run the demo."""
    print("Starting MCP-Enhanced Workflow Demo...")
    asyncio.run(demo_mcp_workflow())
    print("Demo completed.")


if __name__ == "__main__":
    main()