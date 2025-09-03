#!/usr/bin/env python3
"""
Test Command Registration for MCP-Enhanced Tools

This script tests that the new MCP-enhanced commands are properly registered
and can be called through the command system.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from assistents.system_assistent import SystemAssistant
from utils.call_commands import get_system_commands


async def test_command_registration():
    """Test that the new MCP-enhanced commands are properly registered."""
    print("=== Testing MCP-Enhanced Command Registration ===\n")
    
    # Initialize the system assistant
    system_assistant = SystemAssistant(None, None, None)
    
    # Get the registered commands
    commands = get_system_commands(system_assistant)
    
    # List of expected new MCP commands
    expected_mcp_commands = [
        "system info",
        "network info", 
        "process list",
        "search process",
        "battery info"
    ]
    
    print("Checking if new MCP commands are registered:")
    for command in expected_mcp_commands:
        if command in commands:
            print(f"  ✓ '{command}' is registered")
        else:
            print(f"  ✗ '{command}' is NOT registered")
    
    print("\nTesting command execution through the handler:")
    
    # Test commands through the handler
    test_commands = [
        "system info",
        "network info",
        "process list", 
        "search process python",
        "battery info"
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Testing command: '{command}'")
        try:
            result = await system_assistant._handle_command_api(command)
            print(f"   Status: {result.get('status', 'unknown')}")
            if result.get('status') == 'success':
                print(f"   Message: {result.get('message', 'No message')}")
            else:
                print(f"   Error: {result.get('message', 'No error message')}")
        except Exception as e:
            print(f"   Exception: {str(e)}")


def main():
    """Main function to run the tests."""
    print("Starting MCP-Enhanced Command Registration Test...")
    asyncio.run(test_command_registration())
    print("\nTest completed.")


if __name__ == "__main__":
    main()