



from fastapi import APIRouter, Depends, HTTPException, status

from api.config import Settings
from api.dependencies import (get_settings, get_system_assistant,
                              handle_response)
from api.schemas import (ErrorResponse, SystemCommandRequest,
                         SystemCommandResponse)
from assistents.system_assistent import SystemAssistant
from utils.loggers import LoggerSetup  # Import LoggerSetup

router = APIRouter(prefix="/system", tags=["System Assistant"])

# Setup logger for this router
log_setup = LoggerSetup()
logger = log_setup.get_logger("SystemRouter", "system_router.log")


# Use centralized dependency injection




@router.post("/command", response_model=SystemCommandResponse, responses={500: {"model": ErrorResponse}})

async def system_command_endpoint(

    request: SystemCommandRequest,

    system_assistant: SystemAssistant = Depends(get_system_assistant),

    settings: Settings = Depends(get_settings),
):

    try:

        result = await system_assistant._handle_command_api(request.command)

        processed_result = handle_response(result)
        return SystemCommandResponse(**processed_result)

    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code

        raise
    except Exception as e:
        logger.exception(f"Error in /system/command: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )




@router.get("/health")

async def health_check(settings: Settings = Depends(get_settings)):

    """Return availability of optional features and basic runtime info."""

    status = {
        "audio": False,
        "crew": False,
        "torch_cuda": False,
        "ollama": False
    }



    # Check for stable-audio-tools

    try:  # pragma: no cover - depends on runtime env

        from ai_tools.ai_music_generation import _STABLE_AUDIO_AVAILABLE
        status["audio"] = _STABLE_AUDIO_AVAILABLE

    except Exception:

        status["audio"] = False



    # Check for crewai

    try:  # pragma: no cover - depends on runtime env

        status["crew"] = True

    except Exception:

        status["crew"] = False



    # Check torch CUDA

    try:

        import torch

        status["torch_cuda"] = getattr(torch, "cuda", None) is not None and torch.cuda.is_available()

    except Exception:

        status["torch_cuda"] = False



    # Check Ollama connection
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            status["ollama"] = response.status_code == 200
    except Exception:
        status["ollama"] = False

    return {
        "status": "ok",
        "version": settings.api_version,
        "features": status,
        "llm_provider": settings.llm_provider
    }
