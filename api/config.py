import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables with sensible defaults."""

    # Scope env vars to avoid clashes (use MAX_ prefix)
    model_config = SettingsConfigDict(env_prefix="MAX_", extra="ignore")

    # API Settings
    api_title: str = "Max Assistant API"
    api_desc: str = "A central hub for various AI and System functionalities."
    api_version: str = "1.0.0"

    # Server Settings
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8000
    debug: bool = False

    # CORS Settings (typed as Any to avoid env JSON-decoding; coerced via validator)
    cors_origins: Any = [
        "http://localhost",
        "http://localhost:3000",
        "*",
    ]

    # Logging Settings
    log_console_level: str = "INFO"
    log_file_level: str = "DEBUG"
    logs_dir: str = "data/logs"

    # AI Model Settings
    llm_provider: str = "ollama"  # Options: "ollama", "openai", "anthropic", etc.

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    # Anthropic settings
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus"

    # Gemini settings
    gemini_api_key: Optional[str] = None

    # OpenRouter settings
    openrouter_api_key: Optional[str] = None

    # File storage paths
    data_dir: str = "data"
    audio_dir: str = "data/audio"
    text_dir: str = "data/text"

    # Cache settings
    cache_ttl: int = 3600  # seconds
    cache_enabled: bool = True
    cache_type: str = "memory"  # "memory", "redis", "disk"
    cache_max_items: int = 1000

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_timespan: int = 60  # seconds
    rate_limit_block_duration: int = 300  # seconds
    rate_limit_whitelist: Any = ["127.0.0.1", "::1"]

    # Security settings
    enable_auth: bool = False
    auth_secret_key: Optional[str] = None
    token_expiry: int = 86400  # 24 hours in seconds

    # Resource limits
    ai_memory_limit: int = 2048  # MB
    ai_timeout: int = 60  # seconds

    # Model loading optimizations
    lazy_loading: bool = True
    preload_models: List[str] = []
    use_flash_attention: bool = False

    # Other API keys
    user_agent: Optional[str] = None
    vite_serpapi_api_key: Optional[str] = None

    # --- Validators to coerce list-like env vars ---
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return ["http://localhost", "http://localhost:3000", "*"]
            if s.startswith("["):
                import json

                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [p.strip() for p in s.split(",") if p.strip()]
        # If None or unexpected type, fall back to default safe origins
        return ["http://localhost", "http://localhost:3000", "*"]

    @field_validator("rate_limit_whitelist", mode="before")
    @classmethod
    def _parse_whitelist(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return ["127.0.0.1", "::1"]
            if s.startswith("["):
                import json

                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [p.strip() for p in s.split(",") if p.strip()]
        return ["127.0.0.1", "::1"]

    def setup_directories(self) -> None:
        """Ensure that required directories exist."""
        for dir_path in [self.data_dir, self.audio_dir, self.text_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def get_llm_settings(self) -> Dict[str, Any]:
        """Get the settings for the selected LLM provider."""
        providers: Dict[str, Dict[str, Any]] = {
            "ollama": {
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
            },
            "openai": {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            },
        }
        return providers.get(self.llm_provider, {})
