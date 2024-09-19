import asyncio

from ai_tools.ai_research_agent import AIResearchTools, SummarizeTextInput


class AIResearchAgent:
    def __init__(self):
        """Initialize the agent with AIResearchTools."""
        self.research_tools = AIResearchTools()  # Integrate AIResearchTools here

    async def handle_research(self, query):
        """Handle research tasks using AIResearchTools."""
        response = self.research_tools.process_chat(query)
        return response

    async def handle_text_summarization(self, text):
        """Handle text summarization using the custom summarization tool."""
        summarize_tool = self.research_tools.summarize_text_tool
        result = summarize_tool._call(SummarizeTextInput(text=text))
        return result

    # Add more research-related methods as needed


# Example usage
async def run_research_agent():
    agent = AIResearchAgent()

    # Handle research query
    query = "Tell me about the history of AI"
    research_result = await agent.handle_research(query)
    print(f"Research result: {research_result}")

    # Handle text summarization
    text = "Artificial intelligence (AI) is intelligence demonstrated by machines..."
    summarization_result = await agent.handle_text_summarization(text)
    print(f"Summarized text: {summarization_result}")


if __name__ == "__main__":
    asyncio.run(run_research_agent())
