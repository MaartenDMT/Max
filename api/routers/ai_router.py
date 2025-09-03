from fastapi import APIRouter, Depends, HTTPException, status
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
    ErrorResponse,
)
from assistents.ai_assistent import AIAssistant
import asyncio
from utils.loggers import LoggerSetup  # Import LoggerSetup
from api.config import Settings
from api.dependencies import get_ai_assistant, handle_response, get_settings

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Setup logger for this router
log_setup = LoggerSetup()
logger = log_setup.get_logger("AIRouter", "ai_router.log")

# Router uses centralized dependencies from api.dependencies


@router.post("/summarize_youtube", response_model=SummarizeYoutubeResponse, responses={500: {"model": ErrorResponse}})
async def summarize_youtube_endpoint(
    request: SummarizeYoutubeRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._summarize_youtube_api(request.video_url)
        processed_result = handle_response(result)
        return SummarizeYoutubeResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /summarize_youtube: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/chatbot", response_model=ChatbotResponse, responses={500: {"model": ErrorResponse}})
async def chatbot_endpoint(
    request: ChatbotRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._handle_chatbot_api(
            request.mode, request.summary, request.full_text
        )
        # Special handling for chatbot which uses "error" instead of "status"
        if result.get("error"):
            logger.error(f"Error in chatbot processing: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to process chatbot request")
            )
        return ChatbotResponse(status="success", result=result.get("result"))
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /chatbot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/music_generation", response_model=MusicGenerationResponse, responses={500: {"model": ErrorResponse}})
async def music_generation_endpoint(
    request: MusicGenerationRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._make_loop_api(
            request.prompt, request.bpm, request.duration
        )
        processed_result = handle_response(result)
        return MusicGenerationResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /music_generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/research", response_model=ResearchResponse, responses={500: {"model": ErrorResponse}})
async def research_endpoint(
    request: ResearchRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._handle_research_api(request.query)
        processed_result = handle_response(result)
        return ResearchResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/summarize_website", response_model=WebsiteSummarizeResponse, responses={500: {"model": ErrorResponse}})
async def summarize_website_endpoint(
    request: WebsiteSummarizeRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._learn_site_api(request.url, request.question)
        processed_result = handle_response(result)
        return WebsiteSummarizeResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /summarize_website: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/website_research", response_model=WebsiteResearchResponse, responses={500: {"model": ErrorResponse}})
async def website_research_endpoint(
    request: WebsiteResearchRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._research_site_api(
            request.category, request.question
        )
        processed_result = handle_response(result)
        return WebsiteResearchResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /website_research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/writer_task", response_model=WriterTaskResponse, responses={500: {"model": ErrorResponse}})
async def writer_task_endpoint(
    request: WriterTaskRequest,
    ai_assistant: AIAssistant = Depends(get_ai_assistant),
    settings: Settings = Depends(get_settings),
):
    try:
        result = await ai_assistant._handle_writer_task_api(
            request.task_type,
            request.book_description,
            request.num_chapters,
            request.text_content,
        )
        processed_result = handle_response(result)
        return WriterTaskResponse(**processed_result)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.exception(f"Error in /writer_task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
