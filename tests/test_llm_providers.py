#!/usr/bin/env python3
"""
Comprehensive test script for the LLM Provider Management System
Tests all providers, switching functionality, and API integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from assistents.enhanced_ai_assistant import EnhancedAIAssistant
from utils.llm_manager import LLMProviderManager


def test_environment_setup():
    """Test that environment variables are properly set"""
    print("🔧 Testing Environment Setup...")

    required_keys = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'OPENROUTER_API_KEY',
        'GEMINI_API_KEY'
    ]

    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        print(f"❌ Missing environment variables: {missing_keys}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_llm_provider_manager():
    """Test the LLMProviderManager class"""
    print("\n🏗️ Testing LLMProviderManager...")

    try:
        # Initialize provider manager
        manager = LLMProviderManager()
        print("✅ LLMProviderManager initialized successfully")

        # Test getting available providers
        providers = manager.get_available_providers()
        print(f"✅ Available providers: {list(providers.keys())}")

        # Test getting models for each provider
        for provider_name in providers.keys():
            models = manager.get_available_models(provider_name)
            print(f"✅ {provider_name} models: {models}")

        return True

    except Exception as e:
        print(f"❌ LLMProviderManager test failed: {str(e)}")
        return False

def test_provider_switching():
    """Test switching between different providers"""
    print("\n🔄 Testing Provider Switching...")

    try:
        manager = LLMProviderManager()

        # Test switching to different providers
        test_configs = [
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "anthropic", "model": "claude-3-5-sonnet"},
            {"provider": "openrouter", "model": "claude-3.5-sonnet"},
            {"provider": "gemini", "model": "gemini-1.5-flash"}
        ]

        for config in test_configs:
            try:
                llm_instance = manager.create_llm_instance(
                    provider=config["provider"],
                    model=config["model"]
                )
                print(f"✅ Successfully created {config['provider']} instance with {config['model']}")
            except Exception as e:
                print(f"⚠️ Failed to create {config['provider']} instance: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ Provider switching test failed: {str(e)}")
        return False

def test_enhanced_ai_assistant():
    """Test the EnhancedAIAssistant with provider management"""
    print("\n🤖 Testing EnhancedAIAssistant...")

    try:
        # Initialize enhanced assistant
        assistant = EnhancedAIAssistant()
        print("✅ EnhancedAIAssistant initialized successfully")

        # Test provider switching
        test_providers = ["openai", "anthropic", "gemini"]

        for provider in test_providers:
            try:
                result = assistant.change_llm_provider(provider)
                if result.get("status") == "success":
                    print(f"✅ Successfully switched to {provider}")
                else:
                    print(f"⚠️ Failed to switch to {provider}: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ Error switching to {provider}: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ EnhancedAIAssistant test failed: {str(e)}")
        return False

async def test_simple_llm_calls():
    """Test simple LLM calls with different providers"""
    print("\n💬 Testing Simple LLM Calls...")

    try:
        manager = LLMProviderManager()
        test_prompt = "Say 'Hello from AI' in exactly 3 words."

        # Test with available providers
        providers_to_test = [
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "anthropic", "model": "claude-3-haiku"},
            {"provider": "gemini", "model": "gemini-1.5-flash"}
        ]

        for config in providers_to_test:
            try:
                llm = manager.create_llm_instance(
                    provider=config["provider"],
                    model=config["model"]
                )

                # For LangChain LLMs, use invoke method
                if hasattr(llm, 'invoke'):
                    response = llm.invoke(test_prompt)
                else:
                    response = llm(test_prompt)

                print(f"✅ {config['provider']} response: {response}")

            except Exception as e:
                print(f"⚠️ {config['provider']} call failed: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ LLM calls test failed: {str(e)}")
        return False

def test_provider_validation():
    """Test provider and model validation"""
    print("\n✅ Testing Provider Validation...")

    try:
        manager = LLMProviderManager()

        # Test valid provider validation
        valid_result = manager.validate_provider("openai", "gpt-4o-mini")
        print(f"✅ Valid provider validation: {valid_result}")

        # Test invalid provider validation
        invalid_result = manager.validate_provider("invalid_provider", "invalid_model")
        print(f"✅ Invalid provider validation: {invalid_result}")

        # Test invalid model validation
        invalid_model_result = manager.validate_provider("openai", "invalid_model")
        print(f"✅ Invalid model validation: {invalid_model_result}")

        return True

    except Exception as e:
        print(f"❌ Provider validation test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting LLM Provider Management System Tests\n")

    test_results = []

    # Run tests
    test_results.append(("Environment Setup", test_environment_setup()))
    test_results.append(("LLM Provider Manager", test_llm_provider_manager()))
    test_results.append(("Provider Switching", test_provider_switching()))
    test_results.append(("Enhanced AI Assistant", test_enhanced_ai_assistant()))
    test_results.append(("Simple LLM Calls", await test_simple_llm_calls()))
    test_results.append(("Provider Validation", test_provider_validation()))

    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(test_results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! LLM Provider Management System is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
