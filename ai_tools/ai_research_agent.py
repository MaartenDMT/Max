import json
import logging

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun, ReadFileTool, WriteFileTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from utils.llm_manager import LLMManager, LLMConfig # Added LLMConfig import
from decouple import config as decouple_config

llm_config_data = {
    "llm_provider": decouple_config("LLM_PROVIDER", default="ollama"),
    "anthropic_api_key": decouple_config("ANTHROPIC_API_KEY", default=None),
    "openai_api_key": decouple_config("OPENAI_API_KEY", default=None),
    "openrouter_api_key": decouple_config("OPENROUTER_API_KEY", default=None),
    "gemini_api_key": decouple_config("GEMINI_API_KEY", default=None),
}
llm_manager = LLMManager(LLMConfig(**llm_config_data)) # Instantiate LLMConfig


load_dotenv()
logger = logging.getLogger(__name__)


@tool("summarize_text")
def summarize_text(text: str) -> str:
    """Summarize a long text to the first couple of sentences and return JSON string with 'summary'."""
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
        self.create_agentchain()

    def create_agentchain(self):
        """Create an agent chain using multiple tools."""
        model = llm_manager.get_llm()
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
            summarize_text,
        ]
        agent = create_tool_calling_agent(llm=model, tools=tools, prompt=prompt) if model is not None else None
        self.agentExecutor = AgentExecutor(agent=agent, tools=tools) if agent is not None else None

    def process_chat(self, user_input: str) -> dict:
        """Process a user input and get a response from the agent."""
        try:
            if self.agentExecutor is None:
                self.create_agentchain()
            if self.agentExecutor is None:
                return {"error": "LLM not available or failed to initialize research agent."}
            response = self.agentExecutor.invoke(
                {"input": user_input, "chat_history": self.chat_history}
            )
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=response["output"]))
            return {"output": response["output"]}
        except Exception as e:
            return {"error": f"Error processing chat: {str(e)}"}
