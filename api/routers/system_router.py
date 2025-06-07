from fastapi import APIRouter, Depends, HTTPException
from api.schemas import SystemCommandRequest, SystemCommandResponse
from assistents.system_assistent import SystemAssistant
from ai_tools.speech.text_to_speech import TTSModel
import asyncio
from utils.loggers import LoggerSetup  # Import LoggerSetup
from typing import Optional  # Import Optional for type hinting

router = APIRouter(prefix="/system", tags=["System Assistant"])

# Setup logger for this router
log_setup = LoggerSetup()
logger = log_setup.get_logger("SystemRouter", "system_router.log")

# Global instance for singleton pattern
_system_assistant_instance: Optional[SystemAssistant] = None


async def get_system_assistant() -> SystemAssistant:
    global _system_assistant_instance
    if _system_assistant_instance is None:
        logger.info("Initializing SystemAssistant for the first time.")
        tts_model = TTSModel()
        _system_assistant_instance = SystemAssistant(
            tts_model=tts_model, speak=lambda x: x, listen=lambda: ""
        )
    return _system_assistant_instance


@router.post("/command", response_model=SystemCommandResponse)
async def system_command_endpoint(
    request: SystemCommandRequest,
    system_assistant: SystemAssistant = Depends(get_system_assistant),
):
    try:
        result = await system_assistant._handle_command_api(request.command)
        return SystemCommandResponse(**result)
    except Exception as e:
        logger.exception(f"Error in /system/command: {e}")
        raise HTTPException(status_code=500, detail=str(e))
