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

        # Set a default mode for the chatbot
        self.current_mode = "reflecting"  # Default mode

    def add_llm(self, name, model):
        """
        Add a new LLM model to the registry.
        :param name: The mode name (e.g., 'reflecting', 'critique')
        :param model: The model instance (e.g., ReflectingLLM, CritiqueLLM)
        """
        self.llm[name] = model

    async def handle_mode_selection(self):
        """
        Ask the user which LLM mode they want to use (ReflectingAI or CritiqueAI or others in the future).
        """
        try:
            available_modes = ", ".join(self.llm.keys())
            await self._speak(f"Please select the LLM mode: {available_modes}")

            mode = await asyncio.to_thread(input, "LLM mode: ")

            if mode in self.llm:
                self.current_mode = mode
                return f"Mode switched to: {mode.capitalize()}AI"
            else:
                return f"Invalid mode selected. Please choose from: {available_modes}."
        except Exception as e:
            return f"Error selecting mode: {str(e)}"

    async def handle_chatbot_query(self):
        """
        Handle the user's input and route the query to the correct LLM agent based on the current mode.
        """
        try:
            await self._speak(
                f"Please provide your question or content for the {self.current_mode.capitalize()}AI."
            )
            user_input = await asyncio.to_thread(
                input, f"{self.current_mode.capitalize()} input: "
            )

            # Delegate to the LLM associated with the current mode
            return await self.process_with_current_mode(user_input)

        except Exception as e:
            return f"Error processing input: {str(e)}"

    async def process_with_current_mode(self, summary, full_text):
        """
        Process both the summary and full text using the current LLM mode.
        """
        try:
            # Combine both summary and full text for critique
            content_for_critique = f"Summary:\n{summary}\n\nFull Text:\n{full_text}"

            # Pass the combined content to the appropriate LLM
            response = await self.llm[self.current_mode]._handle_query(
                content_for_critique, []
            )

            # If the response is an AIMessage, extract the content
            if isinstance(response, AIMessage):
                return response.content
            return response
        except Exception as e:
            return f"Error processing mode: {str(e)}"


# Example usage in an asyncio loop
async def run_chatbot_agent():
    agent = ChatbotAgent()

    # First, select the LLM mode (reflecting, critique, etc.)
    mode_response = await agent.handle_mode_selection()
    print(mode_response)

    # Then, handle the user's query based on the selected mode
    query_response = await agent.handle_chatbot_query()
    print(query_response)


if __name__ == "__main__":
    asyncio.run(run_chatbot_agent())
