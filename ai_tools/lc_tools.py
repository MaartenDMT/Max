from __future__ import annotations

import asyncio
import json

from langchain_core.tools import tool

from agents.video_agent import VideoProcessingAgent
from ai_tools.ai_music_generation import MusicLoopGenerator
from ai_tools.ai_research_agent import AIResearchTools
# Underlying implementations
from ai_tools.crew_tools import WebPageResearcherTool, WebsiteSummarizerTool
from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.tool_schemas import (MusicGenerationToolInput,
                                   MusicGenerationToolOutput,
                                   ResearchToolInput, ResearchToolOutput,
                                   VideoSummarizerToolInput,
                                   VideoSummarizerToolOutput,
                                   WebResearchToolInput, WebResearchToolOutput,
                                   WebsiteSummarizeToolInput)

# Module-level instances of tool implementations
_website_summarizer_tool_instance = WebsiteSummarizerTool()
_web_page_researcher_tool_instance = WebPageResearcherTool()
_ai_research_tools_instance = AIResearchTools()
_video_processing_agent_instance = VideoProcessingAgent(transcribe=TranscribeFastModel())
_music_loop_generator_instance = MusicLoopGenerator()


@tool(
    "website_summarize",
    return_direct=False,
    args_schema=WebsiteSummarizeToolInput,
)
async def website_summarize(url: str, question: str) -> str:
    """
    Summarize a website for a specific question.
    Inputs:
    - url: The web page URL.
    - question: The question to answer from the page.
    Returns JSON string with keys: summary, keywords or error.
    """
    try:
        result = await _website_summarizer_tool_instance._arun(url=url, question=question)
        if isinstance(result, dict):
            if result.get("status") == "success":
                payload = {
                    "status": "success",
                    "summary": result.get("summary"),
                    "keywords": result.get("keywords"),
                }
                return json.dumps(payload)
            else:
                return json.dumps({"status": "error", "error": result.get("message", "Unknown error")})
        return json.dumps({"status": "error", "error": "Unexpected result format from underlying tool."})
    except Exception as e:
        return json.dumps({"status": "error", "error": f"website_summarize failed: {e}"})


@tool("web_research", return_direct=False)
async def web_research(input: WebResearchToolInput) -> WebResearchToolOutput:
    """
    Perform category-focused web research.
    Inputs:
    - category: research category or topic bucket.
    - question: concrete research question.
    Returns JSON string with key research_result or error.
    """
    try:
        result = await _web_page_researcher_tool_instance._arun(category=input.category, question=input.question)
        if isinstance(result, dict):
            if result.get("status") == "success":
                return WebResearchToolOutput(research_result=result.get("research_result"))
            else:
                return WebResearchToolOutput(status="error", error=result.get("message", "Unknown error"))
        return WebResearchToolOutput(status="error", error="Unexpected result format from underlying tool.")
    except Exception as e:
        return WebResearchToolOutput(status="error", error=f"web_research failed: {e}")


@tool("research", return_direct=False)
async def research(input: ResearchToolInput) -> ResearchToolOutput:
    """
    General research using search and file tools.
    Input:
    - query: research prompt or question.
    Returns JSON string with key output or error.
    """
    try:
        resp = await asyncio.to_thread(_ai_research_tools_instance.process_chat, input.query)
        if isinstance(resp, dict):
            if resp.get("status") == "success":
                return ResearchToolOutput(output=resp.get("output"))
            else:
                return ResearchToolOutput(status="error", error=resp.get("message", "Unknown error"))
        return ResearchToolOutput(status="error", error="Unexpected result format from underlying tool.")
    except Exception as e:
        return ResearchToolOutput(status="error", error=f"research failed: {e}")


@tool("video_summarize", return_direct=False)
async def video_summarize(input: VideoSummarizerToolInput) -> VideoSummarizerToolOutput:
    """
    Summarize a YouTube or Rumble video.
    Input:
    - video_url: URL to the video.
    Returns JSON string with summary/full_text or error.
    """
    try:
        # handle_user_input is synchronous wrapper; run in thread to avoid blocking
        result = await asyncio.to_thread(_video_processing_agent_instance.handle_user_input, input.video_url)
        if isinstance(result, dict):
            if result.get("status") == "success":
                return VideoSummarizerToolOutput(summary=result.get("summary"), full_text=result.get("full_text"))
            else:
                return VideoSummarizerToolOutput(status="error", error=result.get("message", "Unknown error"))
        return VideoSummarizerToolOutput(status="error", error="Unexpected result format from underlying tool.")
    except Exception as e:
        return VideoSummarizerToolOutput(status="error", error=f"video_summarize failed: {e}")


@tool("music_generate", return_direct=False)
async def music_generate(input: MusicGenerationToolInput) -> MusicGenerationToolOutput:
    """
    Generate a music loop.
    Inputs:
    - bpm: beats per minute (40-240)
    - prompt: description/genre
    - duration (optional): seconds (5-300)
    Returns JSON string with status/message/file_path or error.
    """
    try:
        if input.bpm < 40 or input.bpm > 240:
            return MusicGenerationToolOutput(status="error", message="BPM must be between 40 and 240.")
        if not input.prompt or not input.prompt.strip():
            return MusicGenerationToolOutput(status="error", message="Prompt must be provided.")

        # Ensure generator is available
        try:
            if getattr(_music_loop_generator_instance, "model", None) is None:
                return MusicGenerationToolOutput(status="error", message="Music generator is unavailable (optional dependency missing).")
        except Exception:
            return MusicGenerationToolOutput(status="error", message="Music generator is unavailable (optional dependency missing).")

        # Pydantic already handles duration validation
        file_path = await _music_loop_generator_instance.generate_loop(prompt=input.prompt, bpm=input.bpm, duration=input.duration)
        if file_path:
            return MusicGenerationToolOutput(status="success", message=f"Music loop generated: {file_path}", file_path=file_path)
        return MusicGenerationToolOutput(status="error", message="Failed to generate music loop.")
    except Exception as e:
        return MusicGenerationToolOutput(status="error", error=f"music_generate failed: {e}")
