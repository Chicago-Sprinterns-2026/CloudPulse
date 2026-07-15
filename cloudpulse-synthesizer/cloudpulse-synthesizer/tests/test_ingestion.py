from src.ingestion.cleaner import clean_html, normalize_text


def test_normalize_text_removes_extra_whitespace() -> None:
    assert normalize_text("Hello   Cloud\nPulse") == "Hello Cloud Pulse"


def test_clean_html_removes_script_content() -> None:
    html = "<html><script>bad()</script><p>Hello Cloud</p></html>"
    assert clean_html(html) == "Hello Cloud"
