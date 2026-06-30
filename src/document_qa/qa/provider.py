from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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
