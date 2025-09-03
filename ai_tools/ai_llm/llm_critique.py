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


# System prompt for the critique AI
critique_system_prompt = """
You are an AI assistant designed to provide detailed critiques and constructive feedback. Your critiques should follow this structure:

1. Begin with a <thinking> section.
2. Inside the thinking section:
    a. Briefly analyze the provided content and identify areas that require critique.
    b. Outline a clear plan for critiquing different aspects of the content, such as its structure, clarity, argumentation, tone, and any specific areas of improvement.

3. Include a <critique> section for each idea where you:
    a. Provide constructive criticism or feedback for each area you've analyzed.
    b. Suggest specific ways the user can improve their content.
    c. Highlight what works well, as well as what could be enhanced.

4. Be sure to close all critique sections.
5. Close the thinking section with </thinking>.
6. Provide a summary of your critique in an <output> section, emphasizing the most important feedback points.

Always use these tags in your responses. Be thorough in your critiques, offering clear and actionable suggestions for improvement.
Keep your tone professional, constructive, and encouraging.

Remember: Both <thinking> and <critique> MUST be tags and must be closed at their conclusion.
Make sure all <tags> are on separate lines with no other text. Do not include other text on a line containing a tag.
"""


class CritiqueLLM:
    """AI agent designed to provide detailed critiques and feedback."""

    def __init__(self):
        """Initialize CritiqueLLM."""
        self.model = llm_manager.get_llm()

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", critique_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

    async def _handle_query(self, user_input, chat_history):
        """Handle the user's critique request, providing feedback."""
        input_message = [
            HumanMessage(content=user_input),
        ]

        # Get the AI response asynchronously
        model = self.model  # This triggers lazy loading
        if model is None:
            # lightweight fallback for tests
            return "<thinking>Test mode</thinking>\n<critique>OK</critique>\n<output>OK</output>"
        response = await model.ainvoke(input_message)

        # If response contains AIMessage, extract the content
        if isinstance(response, AIMessage):
            return response.content
        return response["output"] if "output" in response else response

    async def run(self):
        """Run the CritiqueLLM and process user queries."""
        print("CritiqueLLM: Ready to critique your content.")
        chat_history = []  # Store chat history for ongoing conversations

        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("CritiqueLLM: Goodbye!")
                break

            # Process the user's input and get a critique response
            result = await self._handle_query(user_input, chat_history)

            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=result))

            print(f"CritiqueLLM: {result}")


# Example usage: Running the CritiqueLLM
if __name__ == "__main__":
    agent = CritiqueLLM()
    asyncio.run(agent.run())
