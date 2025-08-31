from __future__ import annotations

import asyncio
import json
from typing import Optional

from langchain_core.tools import tool

from agents.video_agent import VideoProcessingAgent
from ai_tools.ai_music_generation import MusicLoopGenerator
from ai_tools.ai_research_agent import AIResearchTools

# Underlying implementations
from ai_tools.crew_tools import WebPageResearcherTool, WebsiteSummarizerTool


@tool("website_summarize", return_direct=False)
async def website_summarize(url: str, question: str) -> str:
    """
    Summarize a website for a specific question.
    Inputs:
    - url: The web page URL.
    - question: The question to answer from the page.
    Returns JSON string with keys: summary, keywords or error.
    """
    try:
        tool = WebsiteSummarizerTool()
        result = await tool._arun(url=url, question=question)
        if isinstance(result, dict):
            return json.dumps(result)
        return result
    except Exception as e:
        return json.dumps({"error": f"website_summarize failed: {e}"})


@tool("web_research", return_direct=False)
async def web_research(category: str, question: str) -> str:
    """
    Perform category-focused web research.
    Inputs:
    - category: research category or topic bucket.
    - question: concrete research question.
    Returns JSON string with key research_result or error.
    """
    try:
        tool = WebPageResearcherTool()
        result = await tool._arun(category=category, question=question)
        if isinstance(result, dict):
            return json.dumps(result)
        return result
    except Exception as e:
        return json.dumps({"error": f"web_research failed: {e}"})


@tool("research", return_direct=False)
async def research(query: str) -> str:
    """
    General research using search and file tools.
    Input:
    - query: research prompt or question.
    Returns JSON string with key output or error.
    """
    try:
        agent = AIResearchTools()
        resp = await asyncio.to_thread(agent.process_chat, query)
        return json.dumps(resp)
    except Exception as e:
        return json.dumps({"error": f"research failed: {e}"})


@tool("video_summarize", return_direct=False)
async def video_summarize(video_url: str) -> str:
    """
    Summarize a YouTube or Rumble video.
    Input:
    - video_url: URL to the video.
    Returns JSON string with summary/full_text or error.
    """
    try:
        agent = VideoProcessingAgent(transcribe=None)
        result = await asyncio.to_thread(agent.handle_user_input, video_url)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"video_summarize failed: {e}"})


@tool("music_generate", return_direct=False)
async def music_generate(bpm: int, prompt: str, duration: Optional[int] = None) -> str:
    """
    Generate a music loop.
    Inputs:
    - bpm: beats per minute (40-240)
    - prompt: description/genre
    - duration (optional): seconds (5-300)
    Returns JSON string with status/message/file_path or error.
    """
    try:
        if bpm < 40 or bpm > 240:
            return json.dumps({"status": "error", "message": "BPM must be between 40 and 240."})
        if not prompt or not prompt.strip():
            return json.dumps({"status": "error", "message": "Prompt must be provided."})
        dur = duration if (isinstance(duration, int) and 5 <= duration <= 300) else 30
        gen = MusicLoopGenerator()
        file_path = await asyncio.to_thread(gen.generate_loop, prompt=prompt, bpm=bpm, duration=dur)
        if file_path:
            return json.dumps({"status": "success", "message": f"Music loop generated: {file_path}", "file_path": file_path})
        return json.dumps({"status": "error", "message": "Failed to generate music loop."})
    except Exception as e:
        return json.dumps({"error": f"music_generate failed: {e}"})
