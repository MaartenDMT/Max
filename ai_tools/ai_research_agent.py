import json
import logging
from typing import Any, Dict, Optional, List, Iterator

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    ReadFileTool,
    WikipediaQueryRun,  # Keep import for commenting out
    WolframAlphaQueryRun,  # Keep import for commenting out
    WriteFileTool,
)
from langchain_community.utilities import (
    WikipediaAPIWrapper,  # Keep import for commenting out
    WolframAlphaAPIWrapper,  # Keep import for commenting out
)
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from crewai.tools import BaseTool
from langchain_ollama import ChatOllama
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


load_dotenv()
logger = logging.getLogger(__name__)


class SummarizeTextTool(BaseTool):
    """Custom tool for summarizing text."""

    name: str = "SummarizeTextTool"
    description: str = (
        "A tool for summarizing large blocks of text into shorter summaries."
    )

    def _run(self, text: str) -> str:
        """Perform the text summarization."""
        try:
            sentences = text.split(". ")
            summary = ". ".join(sentences[:2]) + "..." if len(sentences) > 2 else text
            return json.dumps({"summary": summary})
        except Exception as e:
            return json.dumps({"error": f"Error during text summarization: {str(e)}"})


class AIResearchTools:
    """AI Research Agent that uses various tools to answer questions."""

    def __init__(self):
        """Initialize the AIResearchAgent with a set of tools."""
        self.chat_history = []
        self.agentExecutor = None
        # self.wikipedia_tool = WikipediaQueryRun( # Temporarily disabled Wikipedia tool
        #     api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
        # )
        # WolframAlpha requires an app_id. You need to set WOLFRAM_ALPHA_APPID environment variable.
        # self.wolfram_tool = WolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper()) # Disabled Wolfram Alpha
        self.duckduckgo_search_tool = DuckDuckGoSearchRun()
        self.read_file_tool = ReadFileTool()
        self.write_file_tool = WriteFileTool()
        self.summarize_text_tool = SummarizeTextTool()
        self.create_agentchain()

    def create_agentchain(self):
        """Create an agent chain using multiple tools."""
        model = ChatOllama(model="llama3.1", temperature=0.7)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful AI researcher."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        tools = [
            # self.wikipedia_tool, # Temporarily disabled Wikipedia tool
            # self.wolfram_tool, # Disabled Wolfram Alpha
            self.duckduckgo_search_tool,
            self.read_file_tool,
            self.write_file_tool,
            self.summarize_text_tool,
        ]
        agent = create_tool_calling_agent(llm=model, tools=tools, prompt=prompt)
        self.agentExecutor = AgentExecutor(agent=agent, tools=tools)

    def process_chat(self, user_input: str) -> dict:
        """Process a user input and get a response from the agent."""
        try:
            if self.agentExecutor is None:
                self.create_agentchain()
            response = self.agentExecutor.invoke(
                {"input": user_input, "chat_history": self.chat_history}
            )
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=response["output"]))
            return {"output": response["output"]}
        except Exception as e:
            return {"error": f"Error processing chat: {str(e)}"}
