"""Validates the DOCS_PATHS map in app/release_note_links.py.

A wrong path in that map is a 404 for the user, and there's no way to catch it by
reading the code. Run this after editing the map:

    python scripts/check_release_note_links.py

It also flags products that appear in BigQuery but aren't in the map, so you can
see how much of the feed falls through to the data store lookup. Add
`--skip-bigquery` to check URLs only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
import urllib.error
import urllib.request

sys.path.insert(0, ".")

from app.release_note_links import DOCS_BASE, DOCS_PATHS  # noqa: E402

TIMEOUT = 15
UA = "CloudPulse-link-check/1.0"


def check(product: str, path: str) -> tuple[str, str, int | str]:
    url = f"{DOCS_BASE}{path}"
    # HEAD would be cheaper, but devsite doesn't answer it consistently.
    request = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return product, url, response.status
    except urllib.error.HTTPError as error:
        return product, url, error.code
    except Exception as error:
        return product, url, f"{type(error).__name__}: {error}"


def bigquery_products() -> list[str]:
    from app.tools import _bigquery_client

    sql = """
        SELECT product_name, COUNT(*) AS n
        FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
        WHERE product_name IS NOT NULL
        GROUP BY product_name
        ORDER BY n DESC
    """
    return [row.product_name for row in _bigquery_client.query(sql).result()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-bigquery", action="store_true")
    args = parser.parse_args()

    print(f"Checking {len(DOCS_PATHS)} mapped URLs…\n")

    bad = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(check, p, path) for p, path in DOCS_PATHS.items()]
        for future in concurrent.futures.as_completed(futures):
            product, url, status = future.result()
            if status == 200:
                continue
            bad.append((product, url, status))
            print(f"  BROKEN  {status}  {product!r} -> {url}")

    if bad:
        print(f"\n{len(bad)} broken. Fix or remove these — an unmapped product")
        print("falls back to the data store lookup, which is better than a 404.")
    else:
        print("  All mapped URLs return 200.")

    if not args.skip_bigquery:
        print("\nChecking coverage against BigQuery…")
        try:
            products = bigquery_products()
        except Exception as error:
            print(f"  Skipped — BigQuery unavailable: {error}")
            return 1 if bad else 0

        missing = [p for p in products if p not in DOCS_PATHS]
        covered = len(products) - len(missing)
        print(f"  {covered}/{len(products)} products mapped.")
        print(f"  {len(missing)} rely on the data store lookup. Most active 25:")
        for product in missing[:25]:
            print(f"    - {product}")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())