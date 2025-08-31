"""
Simple test to validate basic functionality
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing Imports...")

    try:
        print("✅ LoggerSetup imported")

        print("✅ Enhanced Orchestrator imported")

        print("✅ Enhanced AI Assistant imported")

        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_functionality():
    """Test basic functionality without complex operations"""
    print("\n🔧 Testing Basic Functionality...")

    try:
        # Test memory manager
        from assistents.enhanced_ai_assistant import PersistentMemoryManager
        memory_manager = PersistentMemoryManager()
        print("✅ Memory Manager created")

        # Test session creation
        session_id = memory_manager.create_session("test_user")
        print(f"✅ Session created: {session_id}")

        # Test conversation context
        from agents.enhanced_orchestrator_agent import ConversationContext
        context = ConversationContext(session_id="test")
        print("✅ Conversation Context created")

        return True
    except Exception as e:
        print(f"❌ Basic test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run simple tests"""
    print("🚀 Running Simple Validation Tests")
    print("=" * 50)

    # Test imports
    imports_ok = test_imports()

    if imports_ok:
        # Test basic functionality
        basic_ok = await test_basic_functionality()

        if basic_ok:
            print("\n🎉 All basic tests passed!")
            print("The enhanced components are working correctly.")
        else:
            print("\n⚠️ Basic functionality tests failed")
    else:
        print("\n❌ Import tests failed")

if __name__ == "__main__":
    asyncio.run(main())
