from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

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


class OpenAIProvider:
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
                    {
                        "role": "system",
                        "content": (
                            "Answer the user's question using only the provided document "
                            "context and recent conversation history."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question:\n{prompt.question}\n\n"
                            f"Context:\n{prompt.context}"
                        ),
                    },
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


def build_ai_provider(settings: Settings) -> AIProvider:
    provider_name = settings.ai_provider.strip().lower()
    if provider_name == "fake":
        return FakeAIProvider()
    if provider_name == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError(
                "OPENAI_API_KEY is required when AI_PROVIDER=openai"
            )
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    if provider_name == "deepseek":
        if not settings.deepseek_api_key:
            raise ProviderConfigurationError(
                "DEEPSEEK_API_KEY is required when AI_PROVIDER=deepseek"
            )
        return OpenAIProvider(
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
    raise ProviderConfigurationError(
        f"Unsupported AI_PROVIDER '{settings.ai_provider}'. Supported providers: fake, openai, deepseek"
    )
