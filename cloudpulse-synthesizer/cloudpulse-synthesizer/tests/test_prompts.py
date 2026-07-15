from src.backend.prompt_templates import ONE_PAGER_PROMPT, SYSTEM_PROMPT


def test_system_prompt_requires_sources() -> None:
    assert "source" in SYSTEM_PROMPT.lower()
    assert "invent" in SYSTEM_PROMPT.lower()


def test_one_pager_prompt_has_required_sections() -> None:
    assert "What changed" in ONE_PAGER_PROMPT
    assert "Recommended actions" in ONE_PAGER_PROMPT
    assert "Source references" in ONE_PAGER_PROMPT
