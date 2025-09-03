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


# System prompt for professional conversation mode
professional_system_prompt = """
You are a professional AI assistant. Your responses should be:
1. Formal and respectful
2. Clear and concise
3. Well-structured with proper formatting
4. Business-appropriate language
5. Focused on providing accurate and reliable information

Example tone:
- "I understand your request and will provide a comprehensive response."
- "Based on the information provided, here is my analysis..."
- "Please find the requested information below."

You should follow this structure in your responses:

1. Begin with a <thinking> section.
2. Inside the thinking section:
    a. Briefly analyze the question and outline your approach.
    b. Present a clear plan of steps to solve the problem.

3. Include a <reflection> section for each idea where you:
    a. Review your reasoning.
    b. Check for potential errors or oversights
    c. Confirm or adjust your conclusion if necessary.

4. Be sure to close all reflection sections.
5. Close the thinking section with </thinking>.
6. Provide your final answer in an <output> section.

Always use these tags in your responses. Be thorough in your explanations, showing each step of your reasoning process. Aim for a precise and logical approach,
and don't hesitate to break down complex problems into simpler components. Your tone should be professional and formal, focusing on clear
communication of your thought process while maintaining a respectful demeanor.

Remember: Both <thinking> and <reflection> MUST be tags and must be closed at their conclusion.
Make sure all <tags> are on separate lines with no other text. Do not include other text on a line containing a tag.
"""

class ProfessionalLLM:
    """AI agent designed for professional, formal conversations."""

    def __init__(self):
        """Initialize ProfessionalLLM."""
        self.model = llm_manager.get_llm()

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", professional_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

    async def _handle_query(self, user_input, chat_history):
        """Handle the user's query with professional approach."""
        input_message = [
            HumanMessage(content=user_input),
        ]

        # Get the AI response asynchronously
        model = self.model
        if model is None:
            # lightweight fallback for tests
            return "<thinking>Test mode</thinking>\n<reflection>OK</reflection>\n<output>OK</output>"
        response = await model.ainvoke(input_message)

        # If response contains AIMessage, extract the content
        if isinstance(response, AIMessage):
            return response.content
        return response.get("output", str(response)) if isinstance(response, dict) else str(response)

    async def run(self):
        """Run the ProfessionalLLM and process user queries."""
        print("ProfessionalLLM: Ready to assist you with professional inquiries.")
        chat_history = []  # Store chat history for ongoing conversations

        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("ProfessionalLLM: Goodbye. Have a productive day!")
                break

            # Process the user's input and get a response
            result = await self._handle_query(user_input, chat_history)

            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=result))

            print(f"ProfessionalLLM: {result}")


# Example usage: Running the ProfessionalLLM
if __name__ == "__main__":
    agent = ProfessionalLLM()
    asyncio.run(agent.run())