#!/usr/bin/env python3
"""
Test script to verify that the new chatbot modes work correctly.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from agents.chatbot_agent import ChatbotAgent

async def test_chatbot_modes():
    """Test all chatbot modes"""
    print("Testing chatbot modes...\\n")
    
    # Create chatbot agent
    agent = ChatbotAgent()
    
    # Test content
    test_summary = "This is a test summary."
    test_full_text = "This is a longer test text with more details."
    test_input = "Hello, how are you today?"
    
    # Test all available modes
    modes = list(agent.llm_factories.keys())
    print(f"Available modes: {', '.join(modes)}\\n")
    
    for mode in modes:
        print(f"Testing {mode} mode...")
        try:
            # Test process_with_current_mode
            result = await agent.process_with_current_mode(mode, test_summary, test_full_text)
            if "error" in result:
                print(f"  ✗ Error: {result['error']}")
            else:
                print(f"  ✓ Success: {result['result'][:100]}...")
            
            # Test process_conversation_mode
            conv_result = await agent.process_conversation_mode(mode, test_input)
            if "error" in conv_result:
                print(f"  ✗ Conversation Error: {conv_result['error']}")
            else:
                print(f"  ✓ Conversation Success: {conv_result['result'][:100]}...")
                
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        print()

    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_chatbot_modes())
