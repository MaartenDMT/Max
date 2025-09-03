#!/usr/bin/env python3
"""
Direct Test of MCP-Enhanced System Assistant Tools

This script tests the new MCP-enhanced tools directly without using the workflow.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from assistents.system_assistent import SystemAssistant


async def test_mcp_tools():
    """Test the new MCP-enhanced system assistant tools directly."""
    print("=== Testing MCP-Enhanced System Assistant Tools ===\n")
    
    # Initialize the system assistant
    system_assistant = SystemAssistant(None, None, None)
    
    # Test cases for different MCP-enhanced capabilities
    test_methods = [
        ("_get_system_info_api", "Get comprehensive system information"),
        ("_get_network_info_api", "Get network configuration"),
        ("_get_process_list_api", "List running processes"),
        ("_search_processes_api", "Search for processes containing 'python'", "python"),
        ("_get_battery_info_api", "Get battery information"),
    ]
    
    for i, test in enumerate(test_methods, 1):
        method_name = test[0]
        description = test[1]
        args = test[2:] if len(test) > 2 else []
        
        print(f"{i}. Testing: {description}")
        print(f"   Method: {method_name}")
        
        try:
            # Get the method from the system assistant
            method = getattr(system_assistant, method_name)
            
            # Call the method with appropriate arguments
            if args:
                result = await method(*args)
            else:
                result = await method()
                
            print(f"   Status: {result.get('status', 'unknown')}")
            if result.get('status') == 'success':
                print(f"   Message: {result.get('message', 'No message')}")
                # Show a snippet of the data if available
                data = result.get('data')
                if data:
                    if isinstance(data, dict):
                        print(f"   Data keys: {list(data.keys())}")
                    else:
                        print(f"   Data: {str(data)[:100]}...")
            else:
                print(f"   Error: {result.get('message', 'No error message')}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        print()


def main():
    """Main function to run the tests."""
    print("Starting MCP-Enhanced System Assistant Tools Test...")
    asyncio.run(test_mcp_tools())
    print("Test completed.")


if __name__ == "__main__":
    main()