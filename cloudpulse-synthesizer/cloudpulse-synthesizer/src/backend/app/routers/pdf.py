# routers/pdf.py
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent import run_one_pager_agent

router = APIRouter(prefix="/api", tags=["pdf"])


class PdfRequest(BaseModel):
    product_name: str


async def _get_one_pager_content(product_name: str) -> str:
    try:
        result = await run_one_pager_agent(
            f"Write a one-pager summary for the Google Cloud product "
            f"'{product_name}': current status, recent release notes, "
            f"and any mandatory service announcements (MSAs)."
        )
        return result["answer"] or f"No synthesis content returned for {product_name}."
    except Exception as error:
        return f"⚠️ Failed to generate one-pager for {product_name}: {error}"


def _format_and_upload(content_text: str, product_name: str) -> str:
    """Stub standing in for the teammate's PDF-format + bucket-upload function.

    Swap this out for their real implementation once it's pushed — expected
    shape: (content_text: str, product_name: str) -> pdf_url: str.
    """
    safe_name = product_name.strip().lower().replace(" ", "-")
    return f"https://storage.googleapis.com/cloudpulse-one-pagers/{safe_name}.pdf"


@router.post("/generate-pdf")
async def generate_pdf(request: PdfRequest):
    content_text = await _get_one_pager_content(request.product_name)
    pdf_url = _format_and_upload(content_text, request.product_name)

    return {
        "product_name": request.product_name,
        "content_text": content_text,
        "pdf_url": pdf_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
