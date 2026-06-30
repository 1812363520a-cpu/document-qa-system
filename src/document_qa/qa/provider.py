from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from openai import OpenAI

from document_qa.core.config import Settings


@dataclass(frozen=True)
class ProviderPrompt:
    question: str
    context: str


class AIProvider(Protocol):
    def generate_answer(self, prompt: ProviderPrompt) -> str:
        ...


class FakeAIProvider:
    def generate_answer(self, prompt: ProviderPrompt) -> str:
        return f"Fake answer for '{prompt.question}' based on retrieved document context."


class ProviderConfigurationError(ValueError):
    pass


class AIProviderError(RuntimeError):
    pass


SYSTEM_PROMPT = (
    "Answer the user's question using only the provided document context and "
    "recent conversation history."
)


def _user_prompt(prompt: ProviderPrompt) -> str:
    return f"Question:\n{prompt.question}\n\nContext:\n{prompt.context}"


class OpenAICompatibleProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any = None,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def generate_answer(self, prompt: ProviderPrompt) -> str:
        try:
            response = self._client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _user_prompt(prompt)},
                ],
            )
            answer = response.choices[0].message.content
        except Exception as exc:
            raise AIProviderError(
                "AI provider request failed. Check provider configuration or try again later."
            ) from exc
        return answer or ""

    def _client(self) -> Any:
        if self.client is None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            )
        return self.client


OpenAIProvider = OpenAICompatibleProvider


class AnthropicProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.anthropic.com",
        client: httpx.Client | None = None,
        timeout_seconds: float = 30.0,
        max_tokens: int = 1024,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens

    def generate_answer(self, prompt: ProviderPrompt) -> str:
        try:
            response = self._client().post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": _user_prompt(prompt)},
                    ],
                },
            )
            response.raise_for_status()
            body = response.json()
            answer = "".join(
                item.get("text", "")
                for item in body.get("content", [])
                if item.get("type") == "text"
            )
        except Exception as exc:
            raise AIProviderError(
                "AI provider request failed. Check provider configuration or try again later."
            ) from exc
        return answer

    def _client(self) -> httpx.Client:
        if self.client is None:
            self.client = httpx.Client(timeout=self.timeout_seconds)
        return self.client


class OllamaProvider:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        client: httpx.Client | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.timeout_seconds = timeout_seconds

    def generate_answer(self, prompt: ProviderPrompt) -> str:
        try:
            response = self._client().post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _user_prompt(prompt)},
                    ],
                },
            )
            response.raise_for_status()
            body = response.json()
            answer = body.get("message", {}).get("content") or body.get("response", "")
        except Exception as exc:
            raise AIProviderError(
                "AI provider request failed. Check provider configuration or try again later."
            ) from exc
        return answer

    def _client(self) -> httpx.Client:
        if self.client is None:
            self.client = httpx.Client(timeout=self.timeout_seconds)
        return self.client


def build_ai_provider(settings: Settings) -> AIProvider:
    provider_name = settings.ai_provider.strip().lower()
    if provider_name == "fake":
        return FakeAIProvider()
    if provider_name == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError(
                "OPENAI_API_KEY is required when AI_PROVIDER=openai"
            )
        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    if provider_name == "deepseek":
        if not settings.deepseek_api_key:
            raise ProviderConfigurationError(
                "DEEPSEEK_API_KEY is required when AI_PROVIDER=deepseek"
            )
        return OpenAICompatibleProvider(
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    if provider_name in {"openai_compatible", "openai-compatible"}:
        if not settings.openai_compatible_base_url:
            raise ProviderConfigurationError(
                "OPENAI_COMPATIBLE_BASE_URL is required when AI_PROVIDER=openai_compatible"
            )
        return OpenAICompatibleProvider(
            api_key=settings.openai_compatible_api_key or "not-required",
            model=settings.openai_compatible_model,
            base_url=settings.openai_compatible_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    if provider_name in {"anthropic", "claude"}:
        if not settings.anthropic_api_key:
            raise ProviderConfigurationError(
                "ANTHROPIC_API_KEY is required when AI_PROVIDER=anthropic or claude"
            )
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            base_url=settings.anthropic_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    if provider_name in {"ollama", "local"}:
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    raise ProviderConfigurationError(
        f"Unsupported AI_PROVIDER '{settings.ai_provider}'. Supported providers: "
        "fake, openai, deepseek, openai_compatible, anthropic, claude, ollama, local"
    )
