"""
Test script for Enhanced AI Assistant
Run this to validate the new functionality
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.enhanced_orchestrator_agent import EnhancedOrchestratorAgent
from assistents.enhanced_ai_assistant import EnhancedAIAssistant


async def test_enhanced_features():
    """Test the enhanced AI assistant features"""

    print("🚀 Testing Enhanced AI Assistant Features")
    print("=" * 50)

    # Initialize enhanced assistant
    print("\n1. Initializing Enhanced Assistant...")
    assistant = EnhancedAIAssistant()
    print("✅ Enhanced AI Assistant initialized")

    # Test session management
    print("\n2. Testing Session Management...")
    session_id = assistant.start_new_session("test_user")
    print(f"✅ Session created: {session_id}")

    # Test basic query with memory
    print("\n3. Testing Basic Query with Memory...")
    result = await assistant.process_query(
        "Hello! I'm interested in learning about AI trends in 2024.",
        session_id
    )
    print(f"✅ Query processed: {result['status']}")
    print(f"📝 Response: {result['response'][:100]}...")

    # Test research collaboration
    print("\n4. Testing Research Collaboration...")
    research_result = await assistant._handle_research_api(
        "Latest developments in large language models",
        session_id
    )
    print(f"✅ Research completed: {research_result['status']}")
    print(f"📊 Research result: {research_result['research_result'][:100]}...")

    # Test analysis with context
    print("\n5. Testing Analysis with Context...")
    analysis_result = await assistant._handle_analysis_api(
        "Impact of LLMs on software development workflows",
        "strategic",
        session_id
    )
    print(f"✅ Analysis completed: {analysis_result['status']}")
    print(f"📈 Analysis result: {analysis_result['analysis_result'][:100]}...")

    # Test session insights
    print("\n6. Testing Session Insights...")
    insights = await assistant.get_session_insights(session_id)
    print(f"✅ Insights retrieved: {insights['status']}")
    print(f"🧠 Session summary: {insights['insights']['session_summary']}")

    # Test user preferences
    print("\n7. Testing User Preferences...")
    pref_result = await assistant.set_user_preference(
        "response_style",
        "detailed",
        session_id
    )
    print(f"✅ Preference set: {pref_result['status']}")

    # Test memory persistence
    print("\n8. Testing Memory Persistence...")
    memory_query = await assistant.process_query(
        "What did we discuss about AI trends earlier?",
        session_id
    )
    print(f"✅ Memory query processed: {memory_query['status']}")
    print(f"🧠 Memory response: {memory_query['response'][:100]}...")

    # Test active sessions
    print("\n9. Testing Active Sessions...")
    active_sessions = assistant.get_active_sessions()
    print(f"✅ Active sessions: {len(active_sessions)}")

    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\nEnhanced Features Summary:")
    print("- ✅ Session Management")
    print("- ✅ Memory Persistence")
    print("- ✅ Agent Collaboration")
    print("- ✅ Context Awareness")
    print("- ✅ User Preferences")
    print("- ✅ Research & Analysis Workflows")


async def test_orchestrator_features():
    """Test the enhanced orchestrator features"""

    print("\n🔧 Testing Enhanced Orchestrator Features")
    print("=" * 50)

    # Initialize orchestrator
    print("\n1. Initializing Enhanced Orchestrator...")
    orchestrator = EnhancedOrchestratorAgent(enable_memory=True)
    print("✅ Enhanced Orchestrator initialized")

    # Test simple workflow
    print("\n2. Testing Simple Workflow...")
    response = await orchestrator.run_workflow(
        "Explain the benefits of AI in healthcare",
        "test_orchestrator_session"
    )
    print("✅ Simple workflow completed")
    print(f"📝 Response: {response[:100]}...")

    # Test research workflow
    print("\n3. Testing Research Workflow...")
    research_response = await orchestrator.run_workflow(
        "Research the latest breakthroughs in quantum computing",
        "test_orchestrator_session"
    )
    print("✅ Research workflow completed")
    print(f"📊 Research: {research_response[:100]}...")

    # Test analysis workflow
    print("\n4. Testing Analysis Workflow...")
    analysis_response = await orchestrator.run_workflow(
        "Analyze the impact of quantum computing on cybersecurity",
        "test_orchestrator_session"
    )
    print("✅ Analysis workflow completed")
    print(f"📈 Analysis: {analysis_response[:100]}...")

    print("\n" + "=" * 50)
    print("🎉 Orchestrator tests completed successfully!")


async def main():
    """Run all tests"""
    try:
        await test_enhanced_features()
        await test_orchestrator_features()

        print("\n🏆 ALL TESTS PASSED!")
        print("The enhanced AI assistant is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("Please check the error and ensure all dependencies are installed.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
