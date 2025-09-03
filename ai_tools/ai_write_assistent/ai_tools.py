import asyncio

from decouple import config as decouple_config
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.llm_manager import LLMConfig, LLMManager  # Added LLMConfig import

load_dotenv()

llm_config_data = {
    "llm_provider": decouple_config("LLM_PROVIDER", default="ollama"),
    "anthropic_api_key": decouple_config("ANTHROPIC_API_KEY", default=None),
    "openai_api_key": decouple_config("OPENAI_API_KEY", default=None),
    "openrouter_api_key": decouple_config("OPENROUTER_API_KEY", default=None),
    "gemini_api_key": decouple_config("GEMINI_API_KEY", default=None),
}
llm_manager = LLMManager(LLMConfig(**llm_config_data)) # Instantiate LLMConfig

# Function to load and split documents
async def get_documents(urls):
    """Load and split documents from the given URLs."""
    all_docs = []
    for url in urls:
        loader = WebBaseLoader(url)
        docs = await asyncio.to_thread(loader.load)
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
        splitDocs = splitter.split_documents(docs)
        all_docs.extend(splitDocs)
    return all_docs


embedding_model = None

def _get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = OllamaEmbeddings(model="nomic-embed-text")
    return embedding_model

# Function to create a vector store (ChromaDB) from documents
async def create_db(docs):
    """Create a vector store (ChromaDB) from documents."""
    vectorStore = await asyncio.to_thread(Chroma.from_documents, docs, embedding=_get_embedding_model())
    return vectorStore


# Function to create an AI agent chain with ChromaDB and TavilySearch, now with memory
async def create_agentchain(vectorStore, include_web_search=False):
    """Create an AI agent chain with ChromaDB and TavilySearch and memory."""
    model = llm_manager.get_llm()

    # # Set up memory for conversation context
    # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a friendly assistant called jarvis"),
            MessagesPlaceholder(
                variable_name="chat_history"
            ),  # Memory usage for context
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    retriever = vectorStore.as_retriever(search_kwargs={"k": 3})

    tools = []
    if include_web_search:
        search = TavilySearchResults()
        tools.append(search)

    retrieval_tool = create_retriever_tool(
        retriever,
        "m3_search",
        "use this tool when searching for information about Lord Of Mysteries (LOTM) or Shadow Slave or Games of Thrones (GOT)",
    )

    tools.append(retrieval_tool)

    agent = await asyncio.to_thread(create_tool_calling_agent,
        llm=model,
        tools=tools,
        prompt=prompt,
    )

    agentExecutor = await asyncio.to_thread(AgentExecutor, agent=agent, tools=tools)

    return agentExecutor


tavily_search_instance = None

def _get_tavily_search_instance():
    global tavily_search_instance
    if tavily_search_instance is None:
        tavily_search_instance = TavilySearchResults()
    return tavily_search_instance

# Tool to retrieve information from the internet
async def retrieve_from_internet(query):
    """Retrieve information from the internet using TavilySearch."""
    search = _get_tavily_search_instance()
    response = await asyncio.to_thread(search.run, query)
    return response


# Tool to retrieve information from a vector store
async def retrieve_from_vectorstore(vectorStore, query):
    """Retrieve information from the vector store using ChromaDB."""
    retriever = vectorStore.as_retriever(search_kwargs={"k": 3})
    docs = await asyncio.to_thread(retriever.get_relevant_documents, query)
    return docs
