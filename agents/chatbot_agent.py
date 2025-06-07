import asyncio
import json

from langchain_core.messages import AIMessage

from ai_tools.ai_llm.llm_critique import CritiqueLLM
from ai_tools.ai_llm.llm_reflecting import ReflectingLLM


class ChatbotAgent:
    def __init__(self):
        """
        Initialize the agent with multiple LLM tools.
        The LLMs are stored in a dictionary, making it easy to add more models in the future.
        """

        # Registry to store all available LLMs
        self.llm = {}

        # Add Critique and Reflecting AI agents to the registry
        self.add_llm("reflecting", ReflectingLLM())
        self.add_llm("critique", CritiqueLLM())

    def add_llm(self, name, model):
        """
        Add a new LLM model to the registry.
        :param name: The mode name (e.g., 'reflecting', 'critique')
        :param model: The model instance (e.g., ReflectingLLM, CritiqueLLM)
        """
        self.llm[name] = model

    async def process_with_current_mode(
        self, mode: str, summary: str, full_text: str
    ) -> dict:
        """
        Process both the summary and full text using the specified LLM mode.
        Returns a dictionary with the result or an error.
        """
        try:
            mode = mode.strip().lower()
            if mode not in self.llm:
                return {
                    "error": f"Invalid mode selected. Available modes: {', '.join(self.llm.keys())}."
                }

            # Combine both summary and full text for critique
            content_for_processing = f"Summary:\n{summary}\n\nFull Text:\n{full_text}"

            # Pass the combined content to the appropriate LLM
            response = await self.llm[mode]._handle_query(content_for_processing, [])

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
