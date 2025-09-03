import os
from functools import lru_cache
from typing import Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field  # Added import


class LLMConfig(BaseModel):
    llm_provider: str = Field(default="ollama")
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = Field(default="claude-3-opus-20240229")
    openai_api_key: Optional[str] = None
    openai_model: str = Field(default="gpt-4-turbo")
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = Field(default="anthropic/claude-3-opus")
    gemini_api_key: Optional[str] = None
    gemini_model: str = Field(default="gemini-pro")
    ollama_model: str = Field(default="llama3.1")


class LLMManager:
    """Central provider manager.

    Provides:
    - A cached get_llm(provider) for quick default instances
    - Discovery helpers used in tests: get_available_providers, get_available_models
    - Validation and factory: validate_provider, create_llm_instance
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:  # Updated type hint
        # Build default config from environment when not provided
        if config is None:
            config = LLMConfig(
                llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
                gemini_api_key=os.getenv("GEMINI_API_KEY"),
            )
        self.config = config

    # ----- Discovery -----
    def get_available_providers(self) -> Dict[str, Dict[str, object]]:
        """Return available providers with metadata.

        Keys: provider name
        Values: { models: [..], requires_key: bool }
        """
        return {
            "openai": {
                "models": self.get_available_models("openai"),
                "requires_key": True,
            },
            "anthropic": {
                "models": self.get_available_models("anthropic"),
                "requires_key": True,
            },
            "openrouter": {
                "models": self.get_available_models("openrouter"),
                "requires_key": True,
            },
            "gemini": {
                "models": self.get_available_models("gemini"),
                "requires_key": True,
            },
            "ollama": {
                "models": self.get_available_models("ollama"),
                "requires_key": False,
            },
        }

    def get_available_models(self, provider: str) -> List[str]:
        provider = provider.lower()
        if provider == "openai":
            # Keep this aligned with current OpenAI models exposed via OpenRouter/official
            return [
                "gpt-4o-mini",
                "gpt-4o",
                "o3-mini",
            ]
        if provider == "anthropic":
            return [
                "claude-3-5-sonnet",
                "claude-3-haiku",
                "claude-3-opus-20240229",
            ]
        if provider == "openrouter":
            return [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o-mini",
                "google/gemini-1.5-flash",
            ]
        if provider == "gemini":
            return [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
        if provider == "ollama":
            return [
                "llama3.1",
                "qwen2:0.5b",
                "phi3:mini",
            ]
        return []

    # ----- Validation -----
    def validate_provider(self, provider: str, model: Optional[str] = None) -> Dict[str, object]:
        provider = (provider or "").lower()
        providers = self.get_available_providers()

        if provider not in providers:
            return {"valid": False, "message": f"Unsupported provider: {provider}"}

        # API key checks for hosted providers
        if providers[provider]["requires_key"]:
            key_env = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }[provider]
            if not os.getenv(key_env):
                return {
                    "valid": False,
                    "message": f"Missing required API key: {key_env}",
                }

        if model is None:
            return {"valid": True, "message": "Provider OK"}

        models = set(m.lower() for m in self.get_available_models(provider))
        if model.lower() not in models:
            return {
                "valid": False,
                "message": f"Invalid model '{model}' for provider '{provider}'",
            }
        return {"valid": True, "message": "Provider and model OK"}

    # ----- Factories -----
    @lru_cache(maxsize=None)
    def get_llm(self, provider: Optional[str] = None):  # Updated type hint
        provider = (provider or self.config.llm_provider).lower()
        return self.create_llm_instance(provider=provider)

    def create_llm_instance(self, provider: str, model: Optional[str] = None):
        provider = provider.lower()
        # Resolve model default from config if not provided
        model = model or {
            "openai": self.config.openai_model,
            "anthropic": self.config.anthropic_model,
            "openrouter": self.config.openrouter_model,
            "gemini": self.config.gemini_model,
            "ollama": self.config.ollama_model,
        }.get(provider, None)

        if provider == "anthropic":
            return ChatAnthropic(model=model, api_key=self.config.anthropic_api_key)
        if provider == "openai":
            return ChatOpenAI(model=model, api_key=self.config.openai_api_key)
        if provider == "openrouter":
            return ChatOpenAI(
                model=model,
                api_key=self.config.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        if provider == "gemini":
            return ChatGoogleGenerativeAI(model=model, google_api_key=self.config.gemini_api_key)
        if provider == "ollama":
            return ChatOllama(model=model)
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Backwards-compat alias used in some scripts/documentation
LLMProviderManager = LLMManager


# Example usage:
# from decouple import config as decouple_config
# config = {
#     "llm_provider": decouple_config("LLM_PROVIDER", default="ollama"),
#     "anthropic_api_key": decouple_config("ANTHROPIC_API_KEY", default=None),
#     "openai_api_key": decouple_config("OPENAI_API_KEY", default=None),
#     "openrouter_api_key": decouple_config("OPENROUTER_API_KEY", default=None),
#     "gemini_api_key": decouple_config("GEMINI_API_KEY", default=None),
# }
# llm_manager = LLMManager(config)
# llm = llm_manager.get_llm()
