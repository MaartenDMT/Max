#!/usr/bin/env python3
"""
Quick test script to verify the enhanced LLM provider system
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from assistents.enhanced_ai_assistant import EnhancedAIAssistant
from utils.llm_manager import LLMProviderManager


async def quick_test():
    """Quick test of the enhanced system"""
    print("🚀 Quick LLM Provider System Test")
    print("=" * 40)

    # Test 1: LLM Provider Manager
    print("\n1️⃣ Testing LLM Provider Manager...")
    try:
        manager = LLMProviderManager()
        providers = manager.get_available_providers()
        print(f"✅ Available providers: {list(providers.keys())}")

        # Test validation
        validation = manager.validate_provider("openai")
        print(f"✅ OpenAI validation: {validation['valid']}")

    except Exception as e:
        print(f"❌ LLM Manager test failed: {e}")
        return False

    # Test 2: Enhanced AI Assistant
    print("\n2️⃣ Testing Enhanced AI Assistant...")
    try:
        assistant = EnhancedAIAssistant()
        info = assistant.get_llm_info()
        print(f"✅ Current setup: {info['current_provider']}/{info['current_model']}")

        # Test provider switching
        result = assistant.change_llm_provider("gemini")
        if result.get("status") == "success":
            print("✅ Successfully switched to Gemini")
        else:
            print(f"⚠️ Gemini switch failed: {result.get('message')}")

    except Exception as e:
        print(f"❌ Enhanced Assistant test failed: {e}")
        return False

    # Test 3: Simple Query
    print("\n3️⃣ Testing Query Processing...")
    try:
        # Create a session and test query
        session_id = assistant.create_session("test_user")
        print(f"✅ Created session: {session_id}")

        response = await assistant.query(
            "Hello! Please respond with exactly 5 words.",
            session_id=session_id,
            enable_memory=True
        )

        if response.get("error"):
            print(f"⚠️ Query failed: {response.get('response')}")
        else:
            print(f"✅ Query response: {response.get('response', '')[:50]}...")

    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

    print("\n🎉 All tests completed successfully!")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run the test
    success = asyncio.run(quick_test())

    if success:
        print("\n✅ System is ready for use!")
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
        sys.exit(1)
