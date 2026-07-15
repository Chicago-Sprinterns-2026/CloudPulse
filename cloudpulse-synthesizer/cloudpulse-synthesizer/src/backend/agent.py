"""Main CloudPulse RAG orchestration."""

from dataclasses import dataclass

from src.backend.prompt_templates import (
    ONE_PAGER_PROMPT,
    TROUBLESHOOTING_PROMPT,
)
from src.backend.tools import format_context, search_vertex_documents


@dataclass
class AgentResponse:
    content: str
    sources: list[str]


class CloudPulseAgent:
    """Coordinates retrieval and prompt creation for CloudPulse."""

    def build_one_pager_prompt(
        self,
        product_name: str,
        persona: str = "Cloud Architect",
        priority: str = "Medium",
    ) -> AgentResponse:
        chunks = search_vertex_documents(
            f"{product_name} release notes announcements changes"
        )
        context = format_context(chunks)
        prompt = ONE_PAGER_PROMPT.format(
            persona=persona,
            product_name=product_name,
            priority=priority,
            context=context,
        )
        return AgentResponse(
            content=prompt,
            sources=[chunk.source_url for chunk in chunks],
        )

    def build_chat_prompt(self, question: str) -> AgentResponse:
        chunks = search_vertex_documents(question)
        context = format_context(chunks)
        prompt = TROUBLESHOOTING_PROMPT.format(
            question=question,
            context=context,
        )
        return AgentResponse(
            content=prompt,
            sources=[chunk.source_url for chunk in chunks],
        )

    def generate(self, prompt: str) -> str:
        """Placeholder for Gemini model invocation."""
        # TODO: Connect to Vertex AI Gemini or Gemini Enterprise Agent Platform.
        return prompt
