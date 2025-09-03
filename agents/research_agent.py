import asyncio
import json

from ai_tools.ai_research_agent import AIResearchTools, summarize_text


class AIResearchAgent:
    def __init__(self):
        """Initialize the agent with AIResearchTools."""
        self.research_tools = AIResearchTools()  # Integrate AIResearchTools here

    async def handle_research(self, query: str) -> dict:
        """Handle research tasks using AIResearchTools."""
        try:
            if not isinstance(query, str) or not query.strip():
                return {"status": "error", "message": "Empty research query."}
            # process_chat is synchronous; offload to thread
            response = await asyncio.to_thread(self.research_tools.process_chat, query)
            return {"status": "success", "result": response}
        except Exception as e:
            return {"status": "error", "message": f"Error during research: {str(e)}"}

    async def handle_text_summarization(self, text: str) -> dict:
        """Handle text summarization using the custom summarization tool."""
        try:
            if not isinstance(text, str) or not text.strip():
                return {"status": "error", "message": "Empty text to summarize."}
            # _run is sync; keep sync but offload to thread for API safety
            result = await asyncio.to_thread(summarize_text._run, text=text)
            # result is JSON string; ensure dict return
            try:
                parsed = json.loads(result)
            except Exception:
                parsed = {"summary": str(result)}
            return {"status": "success", **parsed}
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
