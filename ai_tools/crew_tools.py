# f:/Project/Max/ai_tools/crew_tools.py

import asyncio
import json
from pydantic import BaseModel, Field


from crewai.tools import BaseTool

# The Pydantic ...Input classes are no longer needed for native CrewAI tools.
# CrewAI infers arguments from the type hints in the `_run` method signature.


class WebsiteSummarizerTool(BaseTool):
    name: str = "Website Summarizer"
    description: str = "Summarizes a given website URL based on a specific question."
    # REMOVED: The 'args_schema' attribute is for LangChain tools, not native CrewAI tools.

    def _run(self, url: str, question: str) -> str:
        """Runs the tool synchronously."""
        try:
            from ai_tools.ai_doc_webpage_summarizer import WebPageSummarizer

            web_summarizer_instance = WebPageSummarizer()
            result = web_summarizer_instance.summarize_website(
                url, question, summary_length="detailed"
            )
            summary = result.get("summary", "No summary available.")
            keywords = result.get("keywords", [])
            return json.dumps({"summary": summary, "keywords": keywords})
        except Exception as e:
            return json.dumps({"error": f"Error summarizing website: {str(e)}"})


class WebPageResearcherTool(BaseTool):
    name: str = "Web Page Researcher"
    description: str = (
        "Performs research on web pages based on a category and a specific question."
    )
    # REMOVED: The 'args_schema' attribute is for LangChain tools, not native CrewAI tools.

    def _run(self, category: str, question: str) -> str:
        """Runs the tool synchronously."""
        try:
            from ai_tools.ai_webpage_research_agent import AIWebPageResearchAgent

            web_researcher_instance = AIWebPageResearchAgent()
            web_researcher_instance.setup_research(category)
            response = web_researcher_instance.process_chat(question)
            return json.dumps({"research_result": response})
        except Exception as e:
            return json.dumps({"error": f"Error performing web research: {str(e)}"})


# The __main__ block for testing will no longer work because these tools
# don't have the LangChain `.invoke()` method. They must be tested through CrewAI's `.run()`.
# It is safe to remove this block.
