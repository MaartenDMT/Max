#!/usr/bin/env python3
"""
Test for Consolidated AI Assistant

This script tests the consolidated AI assistant to ensure it works correctly
and includes all the best features from both original implementations.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from assistents.ai_assistent import AIAssistant


async def test_consolidated_ai_assistant():
    """Test the consolidated AI assistant."""
    print("=== Testing Consolidated AI Assistant ===\n")
    
    # Initialize the consolidated AI assistant
    # Using None for all parameters since we're not actually using the models in this test
    ai_assistant = AIAssistant(None, None, None, None)
    
    # Test session management
    print("1. Testing session management...")
    session_id = ai_assistant.start_new_session("test_user")
    print(f"   Created session: {session_id}")
    
    # Test setting session
    result = ai_assistant.set_session(session_id)
    print(f"   Set session result: {result}")
    
    # Test processing a query
    print("\n2. Testing query processing...")
    try:
        result = await ai_assistant.process_query("Hello, what can you do?", session_id)
        print(f"   Query result status: {result.get('status')}")
        print(f"   Query result response: {result.get('response', '')[:100]}..." if len(result.get('response', '')) > 100 else f"   Query result response: {result.get('response', '')}")
    except Exception as e:
        print(f"   Query processing error: {str(e)}")
    
    # Test user preferences
    print("\n3. Testing user preferences...")
    try:
        result = await ai_assistant.set_user_preference("analysis_depth", "detailed", session_id)
        print(f"   Preference set result: {result}")
    except Exception as e:
        print(f"   Preference setting error: {str(e)}")
    
    # Test session insights
    print("\n4. Testing session insights...")
    try:
        result = await ai_assistant.get_session_insights(session_id)
        print(f"   Session insights status: {result.get('status')}")
        if result.get('status') == 'success':
            insights = result.get('insights', {})
            print(f"   Session ID: {insights.get('session_id')}")
            print(f"   Topics discussed: {insights.get('key_topics', [])}")
    except Exception as e:
        print(f"   Session insights error: {str(e)}")
    
    # Test legacy methods
    print("\n5. Testing legacy methods...")
    try:
        result = ai_assistant.set_llm_mode("creative")
        print(f"   LLM mode result: {result}")
    except Exception as e:
        print(f"   LLM mode error: {str(e)}")
    
    print("\n=== Test completed ===")


def main():
    """Main function to run the test."""
    print("Starting Consolidated AI Assistant Test...")
    asyncio.run(test_consolidated_ai_assistant())
    print("Test completed.")


if __name__ == "__main__":
    main()