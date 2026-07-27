"""Live Google Cloud release notes.

The data comes from `bigquery-public-data.google_cloud_release_notes.release_notes`
-- the same feed that backs the public release-notes pages, kept current by Google.
Reading it directly is what makes the ledger live, and it replaces the static
`public/release-data/*.json` files, which were a point-in-time dump that went stale
the moment it was written.

Which source is actually in play is decided in `release_notes_source.py` (BigQuery
by default, local fixture files when BigQuery access isn't available). This module
only handles pagination, caching, and serialization.

Two endpoints:

  GET /api/release-notes            paginated feed, newest first
  GET /api/release-notes/products   distinct product names + counts

Pagination is keyset (cursor), not OFFSET. Notes arrive at the top of the feed while
a user is scrolling, and OFFSET would shift every page under them -- duplicating or
skipping rows. The cursor is `<published_date>|<note_id>`, and the next page is
everything strictly older than that point in the sort order.

The table has no primary key, so `note_id` is a hash of the row's content. That
gives a stable sort tiebreaker within a date (many notes share a date), a stable
React key, and dedup for the exact-duplicate rows the table contains.
"""

from __future__ import annotations

import datetime as _dt
import threading
import time
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query

from app.release_note_links import build_note_url
from app.release_notes_source import SOURCE, USING_FIXTURE, fetch_page, fetch_products

router = APIRouter(prefix="/api/release-notes", tags=["release-notes"])

# The first page is what "live" means, so it expires quickly. Older pages are
# immutable history -- Google doesn't rewrite published notes -- so they can sit in
# cache. Both exist mostly so an infinite scroll (or a room full of demo viewers)
# doesn't turn into one BigQuery job per scroll event.
HEAD_TTL_SECONDS = 60
PAGE_TTL_SECONDS = 3600
PRODUCTS_TTL_SECONDS = 3600

MAX_LIMIT = 100


# --------------------------------------------------------------------------- #
# Tiny TTL cache. In-process on purpose: one instance per user session is fine
# here, and it keeps the deploy free of a Redis dependency. If this ever runs on
# many instances and the BigQuery bill matters, the fix is a scheduled query that
# materializes the table into your own dataset -- not a bigger cache.
# --------------------------------------------------------------------------- #
_cache: Dict[Tuple, Tuple[float, Any]] = {}
_cache_lock = threading.Lock()


def _cache_get(key: Tuple) -> Optional[Any]:
    with _cache_lock:
        hit = _cache.get(key)
        if hit is None:
            return None
        expires_at, value = hit
        if expires_at < time.monotonic():
            _cache.pop(key, None)
            return None
        return value


def _cache_put(key: Tuple, value: Any, ttl: int) -> None:
    with _cache_lock:
        _cache[key] = (time.monotonic() + ttl, value)


def _clean(html: Optional[str]) -> str:
    """Release note bodies are HTML fragments; the UI wants plain text."""
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ")
    return " ".join(text.split())


def _parse_cursor(cursor: Optional[str]) -> Tuple[Optional[_dt.date], Optional[str]]:
    if not cursor:
        return None, None
    try:
        raw_date, note_id = cursor.split("|", 1)
        return _dt.date.fromisoformat(raw_date), note_id
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Malformed cursor: {cursor!r}")


def _fetch(*args) -> Any:
    try:
        return fetch_page(*args)
    except HTTPException:
        raise
    except Exception as error:
        print(f"Release notes fetch failed ({SOURCE}): {error}")
        raise HTTPException(
            status_code=502, detail=f"Release notes source unavailable: {error}"
        )


@router.get("")
async def list_release_notes(
    product: Optional[str] = Query(
        None,
        description="Substring match on product name, e.g. 'compute'. Omit for all products.",
    ),
    note_type: Optional[str] = Query(
        None,
        description="Exact release_note_type filter, e.g. BREAKING, DEPRECATED, FEATURE.",
    ),
    cursor: Optional[str] = Query(
        None, description="Opaque cursor from a previous response's next_cursor."
    ),
    limit: int = Query(20, ge=1, le=MAX_LIMIT),
) -> Dict[str, Any]:
    """One page of release notes, newest first, with a cursor for the next page."""
    product_filter = f"%{product.strip()}%" if product and product.strip() else None
    type_filter = note_type.strip().upper() if note_type and note_type.strip() else None
    cursor_date, cursor_id = _parse_cursor(cursor)

    cache_key = ("feed", product_filter, type_filter, cursor, limit)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # One extra row tells us whether another page exists without a second round trip.
    rows = _fetch(product_filter, type_filter, cursor_date, cursor_id, limit + 1)

    has_more = len(rows) > limit
    page = rows[:limit]

    items = [
        {
            "id": row["note_id"],
            "product": row["product_name"],
            "date": row["published_date"].isoformat() if row["published_date"] else None,
            "type": row["release_note_type"] or None,
            "version": row["product_version_name"] or None,
            "update": _clean(row["description"]),
            "url": build_note_url(row["product_name"], row["published_date"]),
        }
        for row in page
    ]

    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = f"{last['published_date'].isoformat()}|{last['note_id']}"

    payload = {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "fetched_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        # So the UI (and anyone reading a demo over your shoulder) can tell whether
        # they're looking at the live feed or the offline snapshot.
        "source": SOURCE,
        "is_live": not USING_FIXTURE,
    }

    _cache_put(cache_key, payload, HEAD_TTL_SECONDS if cursor is None else PAGE_TTL_SECONDS)
    return payload


@router.get("/products")
async def list_products() -> Dict[str, Any]:
    """Every product that has ever published a release note, most active first.

    Replaces the old `public/release-data/manifest.json`.
    """
    cache_key = ("products",)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        rows = fetch_products()
    except Exception as error:
        print(f"Release notes product list failed ({SOURCE}): {error}")
        raise HTTPException(
            status_code=502, detail=f"Release notes source unavailable: {error}"
        )

    payload = {
        "products": [
            {
                "product": row["product"],
                "count": row["count"],
                "latest_date": row["latest_date"].isoformat() if row["latest_date"] else None,
            }
            for row in rows
        ],
        "source": SOURCE,
    }
    _cache_put(cache_key, payload, PRODUCTS_TTL_SECONDS)
    return payload