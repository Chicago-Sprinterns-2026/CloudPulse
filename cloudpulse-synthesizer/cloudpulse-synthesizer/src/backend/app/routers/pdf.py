import io
import uuid
from datetime import datetime, timezone

import markdown as md
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from google.cloud import storage
from pydantic import BaseModel
from xhtml2pdf import pisa

from app.agent import generate_one_pager

router = APIRouter(prefix="/api", tags=["pdf"])

_BUCKET_NAME = "cloudpulse-one-pagers"
_storage_client = storage.Client()

_GOOGLE_BLUE = "#4285F4"
_GOOGLE_RED = "#EA4335"
_GOOGLE_YELLOW = "#FBBC05"
_GOOGLE_GREEN = "#34A853"

# Google Sans/Product Sans aren't available as system fonts here (no TTF
# embedding), so the stack falls back to Arial/Helvetica — the closest
# built-in match to Google's own sans-serif look. Body copy uses Google's
# actual on-surface gray (#3c4043) rather than pure black, which reads
# softer without losing contrast.
_PDF_STYLE = f"""
<style>
  @page {{ size: letter; margin: 0.4in; }}
  body {{ font-family: 'Google Sans', Arial, Helvetica, sans-serif; font-size: 9pt; color: #3c4043; }}
  h1 {{ font-size: 16pt; margin: 0 0 2px; color: #202124; font-weight: bold; }}
  .accent-bar td {{ height: 3px; padding: 0; font-size: 1px; line-height: 1px; }}
  h2 {{
    font-size: 11pt; color: {_GOOGLE_BLUE}; font-weight: bold;
    border-bottom: 1.5px solid {_GOOGLE_BLUE}; padding-bottom: 2px; margin: 8px 0 3px;
  }}
  ul {{ margin: 0 0 3px; padding-left: 16px; }}
  li {{ margin-bottom: 1px; }}
  p {{ margin: 0 0 3px; line-height: 1.25; }}
  strong {{ color: #202124; }}
  a {{ color: {_GOOGLE_BLUE}; }}
</style>
"""

_ACCENT_BAR = f"""
<table class="accent-bar" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
  <tr>
    <td width="25%" style="background-color:{_GOOGLE_BLUE};">&nbsp;</td>
    <td width="25%" style="background-color:{_GOOGLE_RED};">&nbsp;</td>
    <td width="25%" style="background-color:{_GOOGLE_YELLOW};">&nbsp;</td>
    <td width="25%" style="background-color:{_GOOGLE_GREEN};">&nbsp;</td>
  </tr>
</table>
"""


class PdfRequest(BaseModel):
    products: list[str]
    focus: str | None = None
    session_id: str | None = None


async def _get_one_pager_content(products: list[str], focus: str | None, label: str, session_id: str | None) -> str:
    try:
        text = await generate_one_pager(products, focus, session_id)
        return text or f"No synthesis content returned for {label}."
    except Exception as error:
        return f"⚠️ Failed to generate one-pager for {label}: {error}"


def _render_pdf_bytes(content_text: str, title: str) -> bytes:
    body_html = md.markdown(content_text, extensions=["extra"])
    html = (
        f"<html><head>{_PDF_STYLE}</head><body>"
        f"<h1>{title}</h1>{_ACCENT_BAR}{body_html}</body></html>"
    )

    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer)
    if result.err:
        raise RuntimeError(f"PDF rendering failed with {result.err} error(s)")
    return buffer.getvalue()


def _format_and_upload(content_text: str, products: list[str]) -> str | None:
    safe_name = "-".join(p.strip().lower().replace(" ", "-") for p in products)
    blob_name = f"{safe_name}-{uuid.uuid4().hex[:8]}.pdf"

    try:
        pdf_bytes = _render_pdf_bytes(content_text, title=" + ".join(products))
        _storage_client.bucket(_BUCKET_NAME).blob(blob_name).upload_from_string(
            pdf_bytes, content_type="application/pdf"
        )
    except Exception as error:
        print(f"PDF generation/upload error: {error}")
        return None

    # This project's org policy blocks public objects and this identity has
    # no private key to sign a GCS URL directly, so the PDF is served back
    # through our own backend rather than a direct storage.googleapis.com link.
    return f"/api/one-pager-pdf/{blob_name}"


@router.post("/generate-pdf")
async def generate_pdf(request: PdfRequest):
    label = " + ".join(request.products)
    content_text = await _get_one_pager_content(request.products, request.focus, label, request.session_id)
    pdf_url = _format_and_upload(content_text, request.products)

    return {
        "products": request.products,
        "content_text": content_text,
        "pdf_url": pdf_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/one-pager-pdf/{blob_name}")
async def download_one_pager_pdf(blob_name: str):
    try:
        pdf_bytes = _storage_client.bucket(_BUCKET_NAME).blob(blob_name).download_as_bytes()
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"PDF not found: {error}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{blob_name}"'},
    )