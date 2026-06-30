import pytest

from document_qa.core.config import Settings
from document_qa.qa.provider import (
    AIProviderError,
    AnthropicProvider,
    FakeAIProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
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


class FailingCompletions:
    def create(self, **kwargs):
        raise RuntimeError("network timeout")


class RecordingClient:
    def __init__(self, completions=None):
        self.chat = type("Chat", (), {})()
        self.chat.completions = completions or RecordingCompletions()


class RecordingHTTPResponse:
    def __init__(self, payload, should_fail=False):
        self.payload = payload
        self.should_fail = should_fail

    def raise_for_status(self):
        if self.should_fail:
            raise RuntimeError("http error")

    def json(self):
        return self.payload


class RecordingHTTPClient:
    def __init__(self, payload=None, should_fail=False):
        self.payload = payload or {}
        self.should_fail = should_fail
        self.posts = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return RecordingHTTPResponse(self.payload, should_fail=self.should_fail)


def test_provider_factory_uses_fake_provider_by_default():
    provider = build_ai_provider(Settings())

    assert isinstance(provider, FakeAIProvider)


def test_provider_factory_requires_openai_api_key():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        build_ai_provider(Settings(ai_provider="openai", openai_api_key=None))


def test_provider_factory_requires_deepseek_api_key():
    with pytest.raises(ProviderConfigurationError, match="DEEPSEEK_API_KEY"):
        build_ai_provider(Settings(ai_provider="deepseek", deepseek_api_key=None))


def test_provider_factory_requires_openai_compatible_base_url():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_COMPATIBLE_BASE_URL"):
        build_ai_provider(Settings(ai_provider="openai_compatible"))


def test_provider_factory_requires_anthropic_api_key():
    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        build_ai_provider(Settings(ai_provider="claude", anthropic_api_key=None))


def test_provider_factory_rejects_unsupported_provider():
    with pytest.raises(ProviderConfigurationError, match="Unsupported AI_PROVIDER"):
        build_ai_provider(Settings(ai_provider="unknown-provider"))


def test_provider_factory_builds_openai_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="openai",
            openai_api_key="test-key",
            openai_model="test-model",
        )
    )

    assert isinstance(provider, OpenAIProvider)
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.timeout_seconds == 30.0


def test_provider_factory_builds_deepseek_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="deepseek",
            deepseek_api_key="test-key",
            deepseek_model="deepseek-test-model",
            deepseek_base_url="https://example.deepseek.test",
            ai_request_timeout_seconds=8.0,
        )
    )

    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "test-key"
    assert provider.model == "deepseek-test-model"
    assert provider.base_url == "https://example.deepseek.test"
    assert provider.timeout_seconds == 8.0


def test_provider_factory_builds_openai_compatible_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="openai_compatible",
            openai_compatible_api_key="test-key",
            openai_compatible_model="compatible-model",
            openai_compatible_base_url="https://compatible.example/v1",
        )
    )

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.api_key == "test-key"
    assert provider.model == "compatible-model"
    assert provider.base_url == "https://compatible.example/v1"


def test_provider_factory_builds_anthropic_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="anthropic",
            anthropic_api_key="test-key",
            anthropic_model="claude-test-model",
            anthropic_base_url="https://anthropic.example",
        )
    )

    assert isinstance(provider, AnthropicProvider)
    assert provider.api_key == "test-key"
    assert provider.model == "claude-test-model"
    assert provider.base_url == "https://anthropic.example"


def test_provider_factory_builds_ollama_provider_when_configured():
    provider = build_ai_provider(
        Settings(
            ai_provider="ollama",
            ollama_model="llama3.1",
            ollama_base_url="http://ollama.example",
        )
    )

    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3.1"
    assert provider.base_url == "http://ollama.example"


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


def test_openai_provider_wraps_client_errors():
    client = RecordingClient(completions=FailingCompletions())
    provider = OpenAIProvider(
        api_key="unused-with-injected-client",
        model="test-model",
        client=client,
    )

    with pytest.raises(AIProviderError, match="AI provider request failed"):
        provider.generate_answer(
            ProviderPrompt(
                question="What is indexed?",
                context="[doc-1:0]\nIndexed chunks are searched.",
            )
        )


def test_anthropic_provider_sends_prompt_to_messages_api():
    client = RecordingHTTPClient(
        payload={"content": [{"type": "text", "text": "Claude generated answer"}]}
    )
    provider = AnthropicProvider(
        api_key="test-key",
        model="claude-test-model",
        base_url="https://anthropic.example",
        client=client,
    )

    answer = provider.generate_answer(
        ProviderPrompt(
            question="What is indexed?",
            context="[doc-1:0]\nIndexed chunks are searched.",
        )
    )

    assert answer == "Claude generated answer"
    url, call = client.posts[0]
    assert url == "https://anthropic.example/v1/messages"
    assert call["headers"]["x-api-key"] == "test-key"
    assert call["json"]["model"] == "claude-test-model"
    assert "What is indexed?" in call["json"]["messages"][0]["content"]
    assert "Indexed chunks are searched." in call["json"]["messages"][0]["content"]


def test_ollama_provider_sends_prompt_to_local_chat_api():
    client = RecordingHTTPClient(
        payload={"message": {"content": "Ollama generated answer"}}
    )
    provider = OllamaProvider(
        model="llama3.1",
        base_url="http://ollama.example",
        client=client,
    )

    answer = provider.generate_answer(
        ProviderPrompt(
            question="What is indexed?",
            context="[doc-1:0]\nIndexed chunks are searched.",
        )
    )

    assert answer == "Ollama generated answer"
    url, call = client.posts[0]
    assert url == "http://ollama.example/api/chat"
    assert call["json"]["model"] == "llama3.1"
    assert call["json"]["stream"] is False
    assert call["json"]["messages"][0]["role"] == "system"
    assert "What is indexed?" in call["json"]["messages"][1]["content"]
