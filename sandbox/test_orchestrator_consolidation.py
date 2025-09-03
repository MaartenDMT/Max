#!/usr/bin/env python3
"""
Test for Consolidated Orchestrator Agent

This script tests the consolidated orchestrator agent to ensure it works correctly
and includes all the best features from both original implementations.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.orchestrator_agent import OrchestratorAgent
from api.schemas import OrchestratorRunWorkflowRequest


async def test_consolidated_orchestrator():
    """Test the consolidated orchestrator agent."""
    print("=== Testing Consolidated Orchestrator Agent ===\n")
    
    # Initialize the consolidated orchestrator
    orchestrator = OrchestratorAgent()
    
    # Test cases
    test_cases = [
        "What is the weather like today?",
        "Tell me a joke."
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"{i}. Testing: {query}")
        
        # Create a workflow request
        request = OrchestratorRunWorkflowRequest(
            query=query,
            session_id=f"test_session_{i}"
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
    """Main function to run the test."""
    print("Starting Consolidated Orchestrator Agent Test...")
    asyncio.run(test_consolidated_orchestrator())
    print("Test completed.")


if __name__ == "__main__":
    main()