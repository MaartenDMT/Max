# f:/Project/Max/ai_tools/crew_tools.py

import asyncio
import json

# CrewAI optional: provide a minimal BaseTool shim if not installed
try:
    from crewai.tools import BaseTool  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    class BaseTool:  # minimal shim
        name: str = "BaseTool"
        description: str = ""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def _run(self, *args, **kwargs):
            raise NotImplementedError("BaseTool shim: _run not implemented")

        async def _arun(self, *args, **kwargs):
            raise NotImplementedError("BaseTool shim: _arun not implemented")

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
            # WebPageSummarizer.summarize_website is async; run in thread-safe loop
            result = asyncio.run(
                web_summarizer_instance.summarize_website(
                    url, question, summary_length="detailed"
                )
            )
            summary = result.get("summary", "No summary available.")
            keywords = result.get("keywords", [])
            return json.dumps({"summary": summary, "keywords": keywords})
        except Exception as e:
            return json.dumps({"error": f"Error summarizing website: {str(e)}"})

    async def _arun(self, url: str, question: str) -> str:
        try:
            from ai_tools.ai_doc_webpage_summarizer import WebPageSummarizer

            web_summarizer_instance = WebPageSummarizer()
            result = await web_summarizer_instance.summarize_website(
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
            from ai_tools.ai_webpage_research_agent import \
                AIWebPageResearchAgent

            async def _async_run_logic():
                web_researcher_instance = AIWebPageResearchAgent()
                await web_researcher_instance.setup_research(category)
                response = await web_researcher_instance.process_chat(question)
                return json.dumps({"research_result": response})

            return asyncio.run(_async_run_logic())
        except Exception as e:
            return json.dumps({"error": f"Error performing web research: {str(e)}"})

    async def _arun(self, category: str, question: str) -> str:
        try:
            from ai_tools.ai_webpage_research_agent import \
                AIWebPageResearchAgent

            web_researcher_instance = AIWebPageResearchAgent()
            web_researcher_instance.setup_research(category)
            # process_chat is sync; run in thread to avoid blocking loop
            response = await asyncio.to_thread(
                web_researcher_instance.process_chat, question
            )
            return json.dumps({"research_result": response})
        except Exception as e:
            return json.dumps({"error": f"Error performing web research: {str(e)}"})


# The __main__ block for testing will no longer work because these tools
# don't have the LangChain `.invoke()` method. They must be tested through CrewAI's `.run()`.
# It is safe to remove this block.
