import pytest

from document_qa.core.config import Settings
from document_qa.qa.provider import (
    FakeAIProvider,
    OpenAIProvider,
    ProviderConfigurationError,
    ProviderPrompt,
    build_ai_provider,
)


class Message:
    content = "OpenAI generated answer"


class Choice:
    message = Message()


class CompletionResponse:
    choices = [Choice()]


class RecordingCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return CompletionResponse()


class RecordingClient:
    def __init__(self):
        self.chat = type("Chat", (), {})()
        self.chat.completions = RecordingCompletions()


def test_provider_factory_uses_fake_provider_by_default():
    provider = build_ai_provider(Settings())

    assert isinstance(provider, FakeAIProvider)


def test_provider_factory_requires_openai_api_key():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        build_ai_provider(Settings(ai_provider="openai", openai_api_key=None))


def test_provider_factory_requires_deepseek_api_key():
    with pytest.raises(ProviderConfigurationError, match="DEEPSEEK_API_KEY"):
        build_ai_provider(Settings(ai_provider="deepseek", deepseek_api_key=None))


def test_provider_factory_rejects_unsupported_provider():
    with pytest.raises(ProviderConfigurationError, match="Unsupported AI_PROVIDER"):
        build_ai_provider(Settings(ai_provider="claude"))


def test_provider_factory_builds_openai_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="openai",
            openai_api_key="test-key",
            openai_model="test-model",
        )
    )

    assert isinstance(provider, OpenAIProvider)


def test_provider_factory_builds_deepseek_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="deepseek",
            deepseek_api_key="test-key",
            deepseek_model="deepseek-test-model",
            deepseek_base_url="https://example.deepseek.test",
        )
    )

    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "test-key"
    assert provider.model == "deepseek-test-model"
    assert provider.base_url == "https://example.deepseek.test"


def test_openai_provider_sends_question_and_context_to_client():
    client = RecordingClient()
    provider = OpenAIProvider(
        api_key="unused-with-injected-client",
        model="test-model",
        client=client,
    )

    answer = provider.generate_answer(
        ProviderPrompt(
            question="What is indexed?",
            context="[doc-1:0]\nIndexed chunks are searched.",
        )
    )

    assert answer == "OpenAI generated answer"
    call = client.chat.completions.calls[0]
    assert call["model"] == "test-model"
    assert "What is indexed?" in call["messages"][1]["content"]
    assert "Indexed chunks are searched." in call["messages"][1]["content"]
