from fastapi import APIRouter, Depends, HTTPException
from api.schemas import (
    SummarizeYoutubeRequest,
    SummarizeYoutubeResponse,
    ChatbotRequest,
    ChatbotResponse,
    MusicGenerationRequest,
    MusicGenerationResponse,
    ResearchRequest,
    ResearchResponse,
    WebsiteSummarizeRequest,
    WebsiteSummarizeResponse,
    WebsiteResearchRequest,
    WebsiteResearchResponse,
    WriterTaskRequest,
    WriterTaskResponse,
)
from assistents.ai_assistent import AIAssistant
from ai_tools.speech.text_to_speech import TTSModel
from ai_tools.speech.speech_to_text import TranscribeFastModel
import asyncio
from utils.loggers import LoggerSetup  # Import LoggerSetup
from typing import Optional  # Import Optional for type hinting

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Setup logger for this router
log_setup = LoggerSetup()
logger = log_setup.get_logger("AIRouter", "ai_router.log")

# Global instance for singleton pattern
_ai_assistant_instance: Optional[AIAssistant] = (
    None  # Use Optional for initial None assignment
)


async def get_ai_assistant() -> AIAssistant:
    global _ai_assistant_instance
    if _ai_assistant_instance is None:
        logger.info("Initializing AIAssistant for the first time.")
        tts_model = TTSModel()
        transcribe_model = TranscribeFastModel()
        _ai_assistant_instance = AIAssistant(
            tts_model=tts_model,
            transcribe=transcribe_model,
            speak=lambda x: x,
            listen=lambda: "",
        )
    return _ai_assistant_instance


@router.post("/summarize_youtube", response_model=SummarizeYoutubeResponse)
async def summarize_youtube_endpoint(
    request: SummarizeYoutubeRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
):
    try:
        result = await ai_assistant._summarize_youtube_api(request.video_url)
        return SummarizeYoutubeResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /summarize_youtube: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_endpoint(
    request: ChatbotRequest, ai_assistant: AIAssistant = Depends(get_ai_assistant)
):
    try:
        result = await ai_assistant._handle_chatbot_api(
            request.mode, request.summary, request.full_text
        )
        return ChatbotResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /chatbot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/music_generation", response_model=MusicGenerationResponse)
async def music_generation_endpoint(
    request: MusicGenerationRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
):
    try:
        result = await ai_assistant._make_loop_api(
            request.prompt, request.bpm, request.duration
        )
        return MusicGenerationResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /music_generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research", response_model=ResearchResponse)
async def research_endpoint(
    request: ResearchRequest, ai_assistant: AIAssistant = Depends(get_ai_assistant)
):
    try:
        result = await ai_assistant._handle_research_api(request.query)
        return ResearchResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize_website", response_model=WebsiteSummarizeResponse)
async def summarize_website_endpoint(
    request: WebsiteSummarizeRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
):
    try:
        result = await ai_assistant._learn_site_api(request.url, request.question)
        return WebsiteSummarizeResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /summarize_website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/website_research", response_model=WebsiteResearchResponse)
async def website_research_endpoint(
    request: WebsiteResearchRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
):
    try:
        result = await ai_assistant._research_site_api(
            request.category, request.question
        )
        return WebsiteResearchResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /website_research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writer_task", response_model=WriterTaskResponse)
async def writer_task_endpoint(
    request: WriterTaskRequest, ai_assistant: AIAssistant = Depends(get_ai_assistant)
):
    try:
        result = await ai_assistant._handle_writer_task_api(
            request.task_type,
            request.book_description,
            request.num_chapters,
            request.text_content,
        )
        return WriterTaskResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /writer_task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
