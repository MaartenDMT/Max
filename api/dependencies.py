from sqlalchemy.orm import Session
import logging
from functools import lru_cache
from typing import Optional, Callable, Any, Dict


from assistents.ai_assistent import AIAssistant

from assistents.system_assistent import SystemAssistant
from ai_tools.speech.text_to_speech import TTSModel

from ai_tools.speech.speech_to_text import TranscribeFastModel
from utils.database import SessionLocal


# Setup logger
logger = logging.getLogger("dependencies")


# Global instances for singleton pattern

_ai_assistant_instance: Optional[AIAssistant] = None

_system_assistant_instance: Optional[SystemAssistant] = None
_tts_model_instance: Optional[TTSModel] = None

_transcribe_model_instance: Optional[TranscribeFastModel] = None




def get_tts_model() -> TTSModel:
    """
    Lazy load the TTS model only when needed.
    Returns a singleton instance.
    """
    global _tts_model_instance
    if _tts_model_instance is None:
        logger.info("Lazy loading TTS model for the first time")
        _tts_model_instance = TTSModel()
    return _tts_model_instance


def get_transcribe_model() -> TranscribeFastModel:
    """
    Lazy load the transcribe model only when needed.
    Returns a singleton instance.
    """
    global _transcribe_model_instance
    if _transcribe_model_instance is None:
        logger.info("Lazy loading transcribe model for the first time")
        _transcribe_model_instance = TranscribeFastModel()
    return _transcribe_model_instance



def get_settings():
    """
    Get application settings with caching for improved performance.
    Settings will only be loaded once.
    """
    from api.config import Settings
    return Settings()



async def get_ai_assistant() -> AIAssistant:

    """

    FastAPI dependency to get or create the AI Assistant.

    Uses lazy loading patterns for all heavy components.

    """

    global _ai_assistant_instance

    if _ai_assistant_instance is None:

        logger.info("Initializing AIAssistant for the first time with lazy loading")



        # Pass factory functions instead of creating instances

        _ai_assistant_instance = AIAssistant(

            tts_model=lambda: get_tts_model(),

            transcribe=lambda: get_transcribe_model(),

            speak=lambda x: x,

            listen=lambda: "",

        )



    return _ai_assistant_instance


async def get_system_assistant() -> SystemAssistant:
    """
    FastAPI dependency to get or create the System Assistant.
    Uses lazy loading patterns for all heavy components.
    """
    global _system_assistant_instance
    if _system_assistant_instance is None:
        logger.info("Initializing SystemAssistant for the first time with lazy loading")

        # Pass factory functions instead of creating instances
        _system_assistant_instance = SystemAssistant(
            tts_model=lambda: get_tts_model(),
            speak=lambda x: x,
            listen=lambda: "",
        )

    return _system_assistant_instance


def get_db() -> Session:
    """
    FastAPI dependency to get a database session.
    Provides a synchronous database session for API endpoints that need it.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def handle_response(
    result: Dict[str, Any],
    error_status_code: int = 400,
    error_transform: Callable[[Dict[str, Any]], Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Helper function to handle API responses in a consistent way.

    Args:
        result: The result dictionary from an AIAssistant method
        error_status_code: HTTP status code to use for errors
        error_transform: Optional function to transform error responses

    Returns:
        Processed response dictionary or raises HTTPException
    """
    from fastapi import HTTPException

    # Handle error responses
    if result.get("status") == "error" or result.get("error"):
        error_message = result.get("message") or result.get("error") or "Unknown error"
        logger.error(f"Error in AI processing: {error_message}")

        # Apply custom error transformation if provided
        if error_transform:
            transformed = error_transform(result)
            if transformed:
                return transformed

        raise HTTPException(
            status_code=error_status_code,
            detail=error_message
        )

    # For success responses, just return the result
    return result
