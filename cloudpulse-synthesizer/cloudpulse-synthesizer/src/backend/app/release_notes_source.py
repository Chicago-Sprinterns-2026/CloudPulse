"""Where release notes come from: BigQuery (real) or local fixture files (offline).

BigQuery is the point of this feature -- it's what makes the ledger live. But
running it requires `bigquery.jobs.create` plus `serviceusage.services.use` on the
project, and not everyone on the team has both. Rather than leave those people
unable to run the app at all, this module puts both sources behind one interface
so the rest of the backend doesn't care which is in use.

Pick a source with an environment variable:

    RELEASE_NOTES_SOURCE=bigquery   (default)
    RELEASE_NOTES_SOURCE=fixture

Fixture mode reads `frontend-app/data-raw/release_notes_part_*.json` -- the
point-in-time BigQuery dump that used to feed the static UI. It is *stale by
definition*, so it proves the plumbing works, not that the feed is live. Demo on
BigQuery; develop on either.

Both sources return the same shape, so `routers/release_notes.py` is identical
either way:

    {product_name, product_version_name, release_note_type, description,
     published_date: datetime.date, note_id: str}
"""

from __future__ import annotations

import datetime as _dt
import glob
import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

TABLE = "`bigquery-public-data.google_cloud_release_notes.release_notes`"

MAX_BYTES_BILLED = 2 * 1024 ** 3  # 2 GiB

SOURCE = os.getenv("RELEASE_NOTES_SOURCE", "bigquery").strip().lower()
USING_FIXTURE = SOURCE == "fixture"

# src/backend/app/this_file.py -> repo root is four levels up.
def _default_fixture_dir() -> Path:
    """Best guess at frontend-app/data-raw when running from a source checkout.

    Deliberately defensive rather than counting parents: in the Cloud Run image
    the backend is copied to /app with nothing above it, so a fixed parents[3]
    raises IndexError -- at import time, which took the whole service down before
    it could serve one request. Fixture mode isn't usable in the container anyway
    (data-raw lives under frontend-app, which isn't in the backend build context),
    so failing to find it here is harmless: it only surfaces as a clear error if
    someone explicitly asks for fixture mode where the files don't exist.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "frontend-app" / "data-raw"
        if candidate.is_dir():
            return candidate
    return here.parent / "data-raw"  # not found; _load_fixture reports it clearly


FIXTURE_DIR = Path(os.getenv("RELEASE_NOTES_FIXTURE_DIR") or _default_fixture_dir())


# --------------------------------------------------------------------------- #
# Shared
# --------------------------------------------------------------------------- #

def _note_id(product: str, version: str, note_type: str, published: str, body: str) -> str:
    """Content hash used as a stable id and sort tiebreaker.

    Mirrors the SHA256 expression in the BigQuery query. The two sources won't
    produce byte-identical ids (BigQuery's CAST of the date, whitespace in the raw
    dump), and they don't need to -- ids only have to be stable *within* one
    source, since a cursor never crosses sources.
    """
    raw = f"{product}|{version}|{note_type}|{published}|{body}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# BigQuery
# --------------------------------------------------------------------------- #

_FEED_SQL = f"""
WITH notes AS (
  SELECT DISTINCT
    product_name,
    product_version_name,
    release_note_type,
    description,
    DATE(CAST(published_at AS TIMESTAMP)) AS published_date,
    SUBSTR(TO_HEX(SHA256(CONCAT(
      IFNULL(product_name, ''), '|',
      IFNULL(product_version_name, ''), '|',
      IFNULL(release_note_type, ''), '|',
      CAST(published_at AS STRING), '|',
      IFNULL(description, '')
    ))), 1, 16) AS note_id
  FROM {TABLE}
)
SELECT *
FROM notes
WHERE (@product IS NULL OR LOWER(product_name) LIKE LOWER(@product))
  AND (@note_type IS NULL OR release_note_type = @note_type)
  AND (
    @cursor_date IS NULL
    OR published_date < @cursor_date
    OR (published_date = @cursor_date AND note_id < @cursor_id)
  )
ORDER BY published_date DESC, note_id DESC
LIMIT @row_limit
"""

_PRODUCTS_SQL = f"""
SELECT
  product_name,
  COUNT(*) AS note_count,
  MAX(DATE(CAST(published_at AS TIMESTAMP))) AS latest_date
FROM {TABLE}
WHERE product_name IS NOT NULL
GROUP BY product_name
ORDER BY note_count DESC
"""


def _bq_fetch_page(
    product_filter: Optional[str],
    type_filter: Optional[str],
    cursor_date: Optional[_dt.date],
    cursor_id: Optional[str],
    row_limit: int,
) -> List[Dict[str, Any]]:
    from google.cloud import bigquery
    from app.tools import _bigquery_client

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("product", "STRING", product_filter),
            bigquery.ScalarQueryParameter("note_type", "STRING", type_filter),
            bigquery.ScalarQueryParameter("cursor_date", "DATE", cursor_date),
            bigquery.ScalarQueryParameter("cursor_id", "STRING", cursor_id),
            bigquery.ScalarQueryParameter("row_limit", "INT64", row_limit),
        ],
        maximum_bytes_billed=MAX_BYTES_BILLED,
        use_query_cache=True,
    )
    rows = _bigquery_client.query(_FEED_SQL, job_config=job_config).result()
    return [
        {
            "product_name": row.product_name,
            "product_version_name": row.product_version_name,
            "release_note_type": row.release_note_type,
            "description": row.description,
            "published_date": row.published_date,
            "note_id": row.note_id,
        }
        for row in rows
    ]


def _bq_fetch_products() -> List[Dict[str, Any]]:
    from google.cloud import bigquery  # noqa: F401  (kept symmetric with above)
    from app.tools import _bigquery_client

    rows = _bigquery_client.query(_PRODUCTS_SQL).result()
    return [
        {
            "product": row.product_name,
            "count": row.note_count,
            "latest_date": row.latest_date,
        }
        for row in rows
    ]


# --------------------------------------------------------------------------- #
# Fixture
# --------------------------------------------------------------------------- #

_fixture_rows: Optional[List[Dict[str, Any]]] = None
_fixture_lock = threading.Lock()


def _parse_date(raw: Any) -> Optional[_dt.date]:
    if isinstance(raw, _dt.date):
        return raw
    if not raw:
        return None
    try:
        return _dt.date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _load_fixture() -> List[Dict[str, Any]]:
    """Read and normalize the data-raw dump once, sorted the way the feed expects."""
    global _fixture_rows
    with _fixture_lock:
        if _fixture_rows is not None:
            return _fixture_rows

        paths = sorted(glob.glob(str(FIXTURE_DIR / "release_notes*.json")))
        if not paths:
            raise FileNotFoundError(
                f"RELEASE_NOTES_SOURCE=fixture but no release_notes*.json under {FIXTURE_DIR}. "
                "Set RELEASE_NOTES_FIXTURE_DIR to wherever that dump lives."
            )

        seen = set()
        rows: List[Dict[str, Any]] = []

        for path in paths:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            records = payload if isinstance(payload, list) else payload.get("releases", [])

            for record in records:
                # The dump uses the pipeline's field names; tolerate the UI's too.
                product = record.get("product_name") or record.get("product")
                published = _parse_date(record.get("publish_date") or record.get("date"))
                body = record.get("description") or record.get("update") or ""
                if not product or not published:
                    continue

                version = record.get("product_version") or record.get("version") or ""
                note_type = record.get("release_note_type") or record.get("type") or ""

                note_id = _note_id(product, version, note_type, published.isoformat(), body)
                if note_id in seen:
                    continue
                seen.add(note_id)

                rows.append(
                    {
                        "product_name": product,
                        "product_version_name": version or None,
                        "release_note_type": note_type or None,
                        "description": body,
                        "published_date": published,
                        "note_id": note_id,
                    }
                )

        # Same ordering as the SQL: newest first, note_id descending as tiebreaker.
        rows.sort(key=lambda r: (r["published_date"], r["note_id"]), reverse=True)

        print(f"Release notes fixture loaded: {len(rows)} records from {len(paths)} files")
        _fixture_rows = rows
        return _fixture_rows


def _fixture_fetch_page(
    product_filter: Optional[str],
    type_filter: Optional[str],
    cursor_date: Optional[_dt.date],
    cursor_id: Optional[str],
    row_limit: int,
) -> List[Dict[str, Any]]:
    rows = _load_fixture()

    # product_filter arrives as a SQL LIKE pattern (%foo%); strip it back to a substring.
    needle = (product_filter or "").strip("%").lower()

    out: List[Dict[str, Any]] = []
    for row in rows:
        if needle and needle not in row["product_name"].lower():
            continue
        if type_filter and row["release_note_type"] != type_filter:
            continue
        if cursor_date is not None:
            if row["published_date"] > cursor_date:
                continue
            if row["published_date"] == cursor_date and row["note_id"] >= (cursor_id or ""):
                continue
        out.append(row)
        if len(out) >= row_limit:
            break

    return out


def _fixture_fetch_products() -> List[Dict[str, Any]]:
    counts: Dict[str, Dict[str, Any]] = {}
    for row in _load_fixture():
        entry = counts.setdefault(
            row["product_name"], {"product": row["product_name"], "count": 0, "latest_date": None}
        )
        entry["count"] += 1
        if entry["latest_date"] is None or row["published_date"] > entry["latest_date"]:
            entry["latest_date"] = row["published_date"]

    return sorted(counts.values(), key=lambda e: e["count"], reverse=True)


# --------------------------------------------------------------------------- #
# Public interface
# --------------------------------------------------------------------------- #

def fetch_page(
    product_filter: Optional[str],
    type_filter: Optional[str],
    cursor_date: Optional[_dt.date],
    cursor_id: Optional[str],
    row_limit: int,
) -> List[Dict[str, Any]]:
    impl = _fixture_fetch_page if USING_FIXTURE else _bq_fetch_page
    return impl(product_filter, type_filter, cursor_date, cursor_id, row_limit)


def fetch_products() -> List[Dict[str, Any]]:
    return _fixture_fetch_products() if USING_FIXTURE else _bq_fetch_products()