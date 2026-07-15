from src.backend.agent import CloudPulseAgent
from src.backend.tools import RetrievedChunk, format_context


def test_format_context_contains_source() -> None:
    chunks = [
        RetrievedChunk(
            text="Cloud Run added a feature.",
            source_url="https://cloud.google.com/run",
            title="Cloud Run",
        )
    ]

    context = format_context(chunks)

    assert "Cloud Run added a feature." in context
    assert "https://cloud.google.com/run" in context


def test_agent_builds_chat_prompt() -> None:
    response = CloudPulseAgent().build_chat_prompt(
        "How do I troubleshoot Cloud Run?"
    )
    assert "How do I troubleshoot Cloud Run?" in response.content
