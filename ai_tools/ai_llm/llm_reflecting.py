import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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


system_prompt = """
You are an AI assistant designed to provide detailed, step-by-step response. You outputs should follow this structure:

1. Begin with a <thinking> section.
2. Inside the thinking section:
    a. Briefly analyze the question and outline your approach.
    b. Present a clear plan of steps to solve the problem.

3. Icnlude a <reflection> section for each idea where you:
    a. Review your reasoning.
    b. Check for potential errors or oversights
    c. Confirm or adjust your conclusion if necessary.

4. Be sure to close all reflection sections.
5. Close the thinking section with </thinking>.
6. Provide your final answer in an <output> section.

Always use these tags in your responses. Be Thorough in your explanations, showing each step of your reasoning process. Aim to precise and logical approach,
and don't hesitate to break down complex problems into simpler components. Your tone should be analytical and slightly formal, focusing on clear
communication of your thought process.

Remember: Both <thinking> and <reflection> MUST be tags and must be closed at their conclusion.
Make sure all <tags> are on separate lines with no other text. Do not inlude other text on a line containing a tag.

"""


class ReflectingLLM:
    """AI agent designed to provide detailed, step-by-step responses."""

    def __init__(self):
        """Initialize ReflectingAgent."""
        self.model = llm_manager.get_llm()

        # Create a ChatPromptTemplate to use the system prompt and handle history.
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

    async def _handle_query(self, user_input, chat_history):
        """Handle the user's query and reflect on the reasoning process."""
        input_message = [
            HumanMessage(content=user_input),
        ]

        # Get the AI response asynchronously
        model = self.model  # This triggers lazy loading
        if model is None:
            return "<thinking>Test mode</thinking>\n<reflection>OK</reflection>\n<o>OK</o>"
        response = await model.ainvoke(input_message)
        # If response contains AIMessage, extract the content
        if isinstance(response, AIMessage):
            return response.content
        return response.get("output", str(response)) if isinstance(response, dict) else str(response)

    async def run(self):
        """Run the ReflectingAgent and process user queries."""
        print("ReflectingAgent: Ready to process your questions.")
        chat_history = []  # Store chat history for ongoing conversations

        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("ReflectingAgent: Goodbye!")
                break

            # Process the user's input and get a response
            result = await self._handle_query(user_input, chat_history)

            # Append the user's message and the AI response to chat history
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=result))

            print(f"ReflectingAgent: {result}")


# Example usage: Running the ReflectingAgent
if __name__ == "__main__":
    agent = ReflectingLLM()
    asyncio.run(agent.run())
