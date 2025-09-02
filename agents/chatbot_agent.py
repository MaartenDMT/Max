import asyncio
import json

from langchain_core.messages import AIMessage

from ai_tools.ai_llm.llm_critique import CritiqueLLM
from ai_tools.ai_llm.llm_reflecting import ReflectingLLM
from ai_tools.ai_llm.llm_casual import CasualMode
from ai_tools.ai_llm.llm_professional import ProfessionalMode
from ai_tools.ai_llm.llm_creative import CreativeMode
from ai_tools.ai_llm.llm_analytical import AnalyticalMode


class ChatbotAgent:
    def __init__(self):
        """
        Initialize the agent with multiple LLM tools.
        The LLMs are stored in a dictionary, making it easy to add more models in the future.
        Uses lazy loading to only instantiate models when needed.
        """

        # Registry to store all available LLM factory functions
        self.llm_factories = {}
        self.llm_instances = {}

        # Register LLM factory functions
        self.register_llm("reflecting", ReflectingLLM)
        self.register_llm("critique", CritiqueLLM)
        self.register_llm("casual", CasualMode)
        self.register_llm("professional", ProfessionalMode)
        self.register_llm("creative", CreativeMode)
        self.register_llm("analytical", AnalyticalMode)

    def register_llm(self, name, model_class):
        """
        Register a new LLM model factory to the registry.
        :param name: The mode name (e.g., 'reflecting', 'critique')
        :param model_class: The model class (e.g., ReflectingLLM, CritiqueLLM)
        """
        self.llm_factories[name] = model_class

    def get_llm(self, name):
        """
        Get or create an LLM instance by name.
        :param name: The mode name (e.g., 'reflecting', 'critique')
        :return: The model instance, or None if the name is invalid
        """
        if name not in self.llm_factories:
            return None

        if name not in self.llm_instances:
            # Lazy instantiation
            self.llm_instances[name] = self.llm_factories[name]()

        return self.llm_instances[name]

    async def process_with_current_mode(
        self, mode: str, summary: str, full_text: str
    ) -> dict:
        """
        Process both the summary and full text using the specified LLM mode.
        Returns a dictionary with the result or an error.
        """
        try:
            mode = mode.strip().lower()
            if mode not in self.llm_factories:
                return {
                    "error": f"Invalid mode selected. Available modes: {', '.join(self.llm_factories.keys())}."
                }

            # Combine both summary and full text for critique
            content_for_processing = f"Summary:
{summary}

Full Text:
{full_text}"

            # Get the appropriate LLM (lazy loaded) and pass the content
            llm = self.get_llm(mode)
            response = await llm._handle_query(content_for_processing, [])

            # If the response is an AIMessage, extract the content
            if isinstance(response, AIMessage):
                return {"result": response.content}
            return {"result": str(response)}
        except Exception as e:
            return {"error": f"Error processing mode: {str(e)}"}

    async def process_conversation_mode(
        self, mode: str, user_input: str, chat_history: list = None
    ) -> dict:
        """
        Process a conversation using the specified LLM mode.
        Returns a dictionary with the result or an error.
        """
        try:
            mode = mode.strip().lower()
            if mode not in self.llm_factories:
                return {
                    "error": f"Invalid mode selected. Available modes: {', '.join(self.llm_factories.keys())}."
                }

            if chat_history is None:
                chat_history = []

            # Get the appropriate LLM (lazy loaded) and pass the content
            llm = self.get_llm(mode)
            response = await llm._handle_query(user_input, chat_history)

            # If the response is an AIMessage, extract the content
            if isinstance(response, AIMessage):
                return {"result": response.content}
            return {"result": str(response)}
        except Exception as e:
            return {"error": f"Error processing mode: {str(e)}"}


# Example usage (removed interactive parts for API readiness)
# if __name__ == "__main__":
#     async def run_chatbot_agent():
#         agent = ChatbotAgent()
#         # Example of direct call
#         result = await agent.process_with_current_mode("critique", "Short summary.", "Full text content.")
#         print(result)
#     asyncio.run(run_chatbot_agent())
