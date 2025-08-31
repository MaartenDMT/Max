try:
    import langgraph
    print('✅ LangGraph available')
except ImportError:
    print('❌ LangGraph not available')

try:
    import crewai
    print('✅ CrewAI available')
except ImportError:
    print('❌ CrewAI not available')

try:
    import langchain_openai
    print('✅ LangChain OpenAI available')
except ImportError:
    print('❌ LangChain OpenAI not available')

try:
    import pydantic
    print('✅ Pydantic available')
except ImportError:
    print('❌ Pydantic not available')
