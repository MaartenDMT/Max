from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    ReadFileTool,
    WikipediaQueryRun,
    WolframAlphaQueryRun,
    WriteFileTool,
)
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Import the relevant tools from langchain_core.tools and langchain_community
from langchain_core.tools import StructuredTool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field  # Pydantic for input validation

# from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


load_dotenv()


# Custom Structured Tool for text summarization
class SummarizeTextInput(BaseModel):
    """Input schema for SummarizeTextTool."""

    text: str = Field(..., description="The text to summarize")


class SummarizeTextTool(StructuredTool):
    """Custom tool for summarizing text."""

    name = "SummarizeTextTool"
    description = "A tool for summarizing large blocks of text into shorter summaries."
    args_schema = SummarizeTextInput

    def _call(self, args: SummarizeTextInput) -> str:
        """Perform the text summarization."""
        text = args.text
        # Basic summarization logic (this can be extended with more complex NLP models)
        sentences = text.split(". ")
        summary = ". ".join(sentences[:2]) + "..." if len(sentences) > 2 else text
        return summary


class AIResearchTools:
    """AI Research Agent that uses various tools to answer questions or interact with the environment."""

    def __init__(self):
        """Initialize the AIResearchAgent with a set of tools."""
        self.chat_history = []
        self.agentExecutor = None

        # Initialize tools for searching, file operations, and general research
        self.wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        self.wolfram_tool = (
            WolframAlphaQueryRun()
        )  # WolframAlpha query tool for math and science
        self.duckduckgo_search_tool = (
            DuckDuckGoSearchRun()
        )  # DuckDuckGo search tool for privacy-oriented search
        self.read_file_tool = ReadFileTool()  # Read file content
        self.write_file_tool = WriteFileTool()  # Write content to files
        self.summarize_text_tool = SummarizeTextTool()  # Custom text summarization tool

        # Setup the agent chain
        self.create_agentchain()

    def create_agentchain(self):
        """Create an agent chain using multiple tools."""
        model = ChatOllama(
            model="llama3.1",
            temperature=0.7,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful AI researcher."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Combine all tools
        tools = [
            self.wikipedia_tool,
            self.wolfram_tool,
            self.duckduckgo_search_tool,
            self.read_file_tool,
            self.write_file_tool,
            self.summarize_text_tool,  # Add custom summarization tool
        ]

        # Create the agent with the tools
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


if __name__ == "__main__":
    agent = AIResearchTools()

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        response = agent.process_chat(user_input)
        print(f"Assistant: {response}")
