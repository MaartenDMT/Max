from dotenv import load_dotenv

load_dotenv()
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Function to load and split documents
def get_documents(urls):
    """Load and split documents from the given URLs."""
    all_docs = []
    for url in urls:
        loader = WebBaseLoader(url)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
        splitDocs = splitter.split_documents(docs)
        all_docs.extend(splitDocs)
    return all_docs


# Function to create a vector store (ChromaDB) from documents
def create_db(docs):
    """Create a vector store (ChromaDB) from documents."""
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    vectorStore = Chroma.from_documents(docs, embedding=embedding)
    return vectorStore


# Function to create an AI agent chain with ChromaDB and TavilySearch, now with memory
def create_agentchain(vectorStore, include_web_search=False):
    """Create an AI agent chain with ChromaDB and TavilySearch and memory."""
    model = ChatOllama(model="llama3.1", temperature=0.7, num_predict=-1)

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

    agent = create_tool_calling_agent(
        llm=model,
        tools=tools,
        prompt=prompt,
    )

    agentExecutor = AgentExecutor(agent=agent, tools=tools)

    return agentExecutor


# Tool to retrieve information from the internet
def retrieve_from_internet(query):
    """Retrieve information from the internet using TavilySearch."""
    search = TavilySearchResults()
    response = search.run(query)
    return response


# Tool to retrieve information from a vector store
def retrieve_from_vectorstore(vectorStore, query):
    """Retrieve information from the vector store using ChromaDB."""
    retriever = vectorStore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.get_relevant_documents(query)
    return docs
