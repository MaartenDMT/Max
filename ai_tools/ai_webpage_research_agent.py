import json

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

sytem_prompt = """
You are an advanced research assistant called "Researcher". Your goal is to assist the user in extracting, analyzing, and presenting information 
in a clear and concise manner. You are capable of processing large amounts of web-based information, drawing from specific sources, and presenting 
it in well-organized responses.

Your responses should follow this structure:
    
1. **Introduction**: 
   - Briefly introduce the topic or provide context based on the user's question.
   
2. **Research Steps**:
   - Clearly outline the steps you will take to gather the necessary information (e.g., extracting key information from specific websites, using tools to analyze data).
   - Use relevant external sources (like Wikipedia or web documents) to provide a well-rounded answer.
   
3. **Analysis**:
   - Provide in-depth analysis and insights based on the gathered information.
   - When applicable, cite specific parts of the sources to strengthen your response.
   - If there are limitations to the information, explain them clearly.

4. **Conclusion**:
   - Summarize the key points from your analysis.
   - Provide any recommendations or follow-up actions that may help the user further.

Be formal and professional in your tone, but friendly and approachable in your explanations. Always aim for precision, and break down complex topics into easily understandable components.

Remember to:
- Cross-reference relevant documents and sources.
- Always check for the reliability and accuracy of the information before presenting it.
- For ambiguous or incomplete queries, ask the user for clarification.

Make sure your answer is well-structured, informative, and thorough, and that it adheres to the user's specific request.
"""


class AIWebPageResearchAgent:
    def __init__(self, urls_file="data/json/research_urls.json"):
        """Initialize the AIWebPageResearchAgent with URLs from a JSON file."""
        self.urls = self.load_urls(urls_file)
        self.chat_history = []
        self.vectorStore = None
        self.agentExecutor = None

    def load_urls(self, urls_file):
        """Load URLs from the given JSON file."""
        with open(urls_file, "r") as f:
            return json.load(f)

    def get_documents(self, category):
        """Get documents from a list of URLs in a specific category."""
        if category not in self.urls:
            raise ValueError(f"Category '{category}' not found in URLs.")

        urls = self.urls[category]
        all_docs = []
        for url in urls:
            loader = WebBaseLoader(url)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
            splitDocs = splitter.split_documents(docs)
            all_docs.extend(splitDocs)
        return all_docs

    def create_db(self, docs):
        """Create a vector store from the documents."""
        embedding = OllamaEmbeddings(model="nomic-embed-text")
        vectorStore = Chroma.from_documents(docs, embedding=embedding)
        return vectorStore

    def create_agentchain(self):
        """Create an agent chain using the vector store."""
        model = ChatOllama(
            model="llama3.1",
            temperature=0.7,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", sytem_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        retriever = self.vectorStore.as_retriever(search_kwargs={"k": 3})
        wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        retrieval_tool = create_retriever_tool(
            retriever,
            "m3_search",
            "use this tool when searching for information about the research in the urls",
        )

        tools = [retrieval_tool, wikipedia_tool]

        agent = create_tool_calling_agent(
            llm=model,
            tools=tools,
            prompt=prompt,
        )

        self.agentExecutor = AgentExecutor(agent=agent, tools=tools)

    def process_chat(self, user_input):
        """Process a user input and get a response from the agent."""
        response = self.agentExecutor.invoke(
            {"input": user_input, "chat_history": self.chat_history}
        )
        self.chat_history.append(HumanMessage(content=user_input))
        self.chat_history.append(AIMessage(content=response["output"]))
        return response["output"]

    def setup_research(self, category):
        """Set up the research process by loading documents and creating the agent chain."""
        docs = self.get_documents(category)
        self.vectorStore = self.create_db(docs)
        self.create_agentchain()

    def add_research_category(self, category_name, urls):
        """Add a new research category with its URLs."""
        self.urls[category_name] = urls
        self.save_urls("urls.json")

    def save_urls(self, urls_file):
        """Save the updated URLs back to the JSON file."""
        with open(urls_file, "w") as f:
            json.dump(self.urls, f, indent=4)


if __name__ == "__main__":
    agent = AIWebPageResearchAgent()

    # Choose a category to research (book_research_urls or langchain_research_urls)
    category = "book_research_urls"
    agent.setup_research(category)

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        response = agent.process_chat(user_input)
        print(f"Assistant: {response}")
