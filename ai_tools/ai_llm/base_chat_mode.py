import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.llm_manager import LLMManager, LLMConfig
from decouple import config as decouple_config

llm_config_data = {
    "llm_provider": decouple_config("LLM_PROVIDER", default="ollama"),
    "anthropic_api_key": decouple_config("ANTHROPIC_API_KEY", default=None),
    "openai_api_key": decouple_config("OPENAI_API_KEY", default=None),
    "openrouter_api_key": decouple_config("OPENROUTER_API_KEY", default=None),
    "gemini_api_key": decouple_config("GEMINI_API_KEY", default=None),
}
llm_manager = LLMManager(LLMConfig(**llm_config_data))


class BaseChatMode:
    """Base class for different chat modes."""
    
    def __init__(self, system_prompt: str):
        """Initialize with a specific system prompt."""
        self.model = llm_manager.get_llm()
        self.system_prompt = system_prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

    async def _handle_query(self, user_input, chat_history):
        """Handle the user's query with the specific mode's approach."""
        input_message = {"input": user_input, "chat_history": chat_history}
        
        # Get the AI response asynchronously
        model = self.model
        if model is None:
            return "Test mode response"
        response = await model.ainvoke(input_message)
        return response.get("output", str(response)) if isinstance(response, dict) else str(response)