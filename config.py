"""Runtime settings. Override via environment variables.

The extractor talks to any OpenAI-compatible chat endpoint, so switching
providers is just a matter of picking a preset (TAX_EXTRACTOR_PROVIDER) or
setting the base URL / model / key env vars directly.

Free options (as of late 2026 — model names change, check the provider's docs):
  gemini  Google AI Studio free tier. Key: https://aistudio.google.com/apikey
  groq    Groq free tier.             Key: https://console.groq.com/keys
  ollama  Runs locally, fully free and private. Install: https://ollama.com
"""

import os
from dataclasses import dataclass

PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.5-flash-lite",  # gemini-2.5-flash is closed to new keys; try gemini-3.8-flash when not overloaded
        "key_env": "GEMINI_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1",
        "key_env": None,  # no key needed locally
    },
}


@dataclass(frozen=True)
class Settings:
    provider: str
    base_url: str
    model: str
    api_key: str
    max_retries: int  # re-ask the model if its JSON fails schema validation


def load_settings() -> Settings:
    provider = os.getenv("TAX_EXTRACTOR_PROVIDER", "gemini")
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}; choose from {list(PROVIDERS)}")
    preset = PROVIDERS[provider]
    key_env = preset["key_env"]
    return Settings(
        provider=provider,
        base_url=os.getenv("TAX_EXTRACTOR_BASE_URL", preset["base_url"]),
        model=os.getenv("TAX_EXTRACTOR_MODEL", preset["model"]),
        api_key=(os.getenv(key_env, "") if key_env else "ollama"),
        max_retries=int(os.getenv("TAX_EXTRACTOR_MAX_RETRIES", "2")),
    )
