import asyncio

from ai_tools.ai_research_agent import AIResearchTools  # Removed SummarizeTextInput


class AIResearchAgent:
    def __init__(self):
        """Initialize the agent with AIResearchTools."""
        self.research_tools = AIResearchTools()  # Integrate AIResearchTools here

    async def handle_research(self, query: str) -> dict:
        """Handle research tasks using AIResearchTools."""
        try:
            response = self.research_tools.process_chat(query)
            return {"status": "success", "result": response}
        except Exception as e:
            return {"status": "error", "message": f"Error during research: {str(e)}"}

    async def handle_text_summarization(self, text: str) -> dict:
        """Handle text summarization using the custom summarization tool."""
        try:
            summarize_tool = self.research_tools.summarize_text_tool
            result = summarize_tool._run(text=text)  # Call _run directly
            return {"status": "success", "summary": result}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during text summarization: {str(e)}",
            }

    # Add more research-related methods as needed


# Example usage (removed interactive parts for API readiness)
# async def run_research_agent():
#     agent = AIResearchAgent()

#     # Handle research query
#     # query = "Tell me about the history of AI"
#     # research_result = await agent.handle_research(query)
#     # print(f"Research result: {research_result}")

#     # Handle text summarization
#     # text = "Artificial intelligence (AI) is intelligence demonstrated by machines..."
#     # summarization_result = await agent.handle_text_summarization(text)
#     # print(f"Summarized text: {summarization_result}")


# if __name__ == "__main__":
#     asyncio.run(run_research_agent())
