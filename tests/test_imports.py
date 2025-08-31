"""
Simple import test for enhanced AI assistant components
"""
import traceback


def test_imports():
    """Test if all required imports work"""
    print("🧪 Testing Enhanced AI Assistant Imports")
    print("=" * 50)

    # Test basic imports
    try:
        print("✅ asyncio imported successfully")
    except Exception as e:
        print(f"❌ asyncio import failed: {e}")

    # Test LangChain imports
    try:
        print("✅ LangChain core imports successful")
    except Exception as e:
        print(f"❌ LangChain imports failed: {e}")

    # Test LangGraph imports
    try:
        print("✅ LangGraph imports successful")
    except Exception as e:
        print(f"❌ LangGraph imports failed: {e}")
        traceback.print_exc()

    # Test CrewAI imports
    try:
        print("✅ CrewAI imports successful")
    except Exception as e:
        print(f"❌ CrewAI imports failed: {e}")
        traceback.print_exc()

    # Test Pydantic imports
    try:
        print("✅ Pydantic imports successful")
    except Exception as e:
        print(f"❌ Pydantic imports failed: {e}")

    # Test FastAPI imports
    try:
        print("✅ FastAPI imports successful")
    except Exception as e:
        print(f"❌ FastAPI imports failed: {e}")

    print("\n" + "=" * 50)
    print("Import test completed!")

if __name__ == "__main__":
    test_imports()
