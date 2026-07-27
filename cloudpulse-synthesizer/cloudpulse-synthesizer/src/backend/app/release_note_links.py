"""Resolves a Google Cloud product name to the public release-notes page for it.

BigQuery's public release-notes table (`bigquery-public-data.google_cloud_release_notes.release_notes`)
tells us the product name, the date, and the body of every note -- but not the URL
of the page it was published on. This module fills that gap so the ledger in the UI
can link each note back to the official docs.

Three layers, cheapest first:

1. `DOCS_PATHS` -- a hand-checked map of product name -> docs path. Instant, no network.
2. The Vertex AI Search data store (`google-cloud-official-docs`), which already
   indexes `docs.cloud.google.com/release-notes*`. We ask it for
   "<product> release notes" and take the first result whose URL path actually
   ends in `release-notes`. Results are memoized for the process lifetime.
3. The aggregated all-products page. Always a real page, just not product-specific.

Every URL gets a `#July_16_2026`-style anchor appended, which is the anchor devsite
generates for the date headings on these pages. Notes older than roughly a year live
on the `-archive` page instead, so the anchor won't resolve for those -- the page
still loads, it just opens at the top.
"""

from __future__ import annotations

import datetime as _dt
import re
from typing import Dict, Optional
from urllib.parse import urlparse

DOCS_BASE = "https://docs.cloud.google.com"
ALL_PRODUCTS_URL = f"{DOCS_BASE}/release-notes"

# Product name (as it appears in the BigQuery table) -> docs path.
# Keep this sorted by area so it stays reviewable. Run
# `python scripts/check_release_note_links.py` after editing to catch typos --
# a wrong path here is a 404 in the user's face.
DOCS_PATHS: Dict[str, str] = {
    # Compute
    "Compute Engine": "/compute/docs/release-notes",
    "Google Kubernetes Engine": "/kubernetes-engine/docs/release-notes",
    "Cloud Run": "/run/docs/release-notes",
    "Cloud Run Functions": "/run/docs/release-notes",
    "Batch": "/batch/docs/release-notes",
    "Cloud TPU": "/tpu/docs/release-notes",
    "Cloud Workstations": "/workstations/docs/release-notes",
    "Bare Metal Solution": "/bare-metal/docs/release-notes",
    "Container-Optimized OS": "/container-optimized-os/docs/release-notes",
    "Google Cloud VMware Engine": "/vmware-engine/docs/release-notes",
    "Guest environment": "/compute/docs/images/guest-environment/release-notes",
    # Storage
    "Cloud Storage": "/storage/docs/release-notes",
    "Filestore": "/filestore/docs/release-notes",
    "NetApp Volumes": "/netapp/volumes/docs/release-notes",
    "Storage Transfer Service": "/storage-transfer/docs/release-notes",
    "Transfer Appliance": "/transfer-appliance/docs/release-notes",
    "Backup and DR": "/backup-disaster-recovery/docs/release-notes",
    # Databases
    "BigQuery": "/bigquery/docs/release-notes",
    "Bigtable": "/bigtable/docs/release-notes",
    "Spanner": "/spanner/docs/release-notes",
    "Firestore": "/firestore/docs/release-notes",
    "AlloyDB": "/alloydb/docs/release-notes",
    "Datastore": "/datastore/docs/release-notes",
    "Cloud SQL for MySQL": "/sql/docs/mysql/release-notes",
    "Cloud SQL for PostgreSQL": "/sql/docs/postgres/release-notes",
    "Cloud SQL for SQL Server": "/sql/docs/sqlserver/release-notes",
    "Memorystore for Redis": "/memorystore/docs/redis/release-notes",
    "Memorystore for Redis Cluster": "/memorystore/docs/cluster/release-notes",
    "Memorystore for Memcached": "/memorystore/docs/memcached/release-notes",
    "Memorystore for Valkey": "/memorystore/docs/valkey/release-notes",
    "Cloud Database Migration Service": "/database-migration/docs/release-notes",
    "Datastream": "/datastream/docs/release-notes",
    # Data & analytics
    "Dataflow": "/dataflow/docs/release-notes",
    "Dataform": "/dataform/docs/release-notes",
    "Dataproc Metastore": "/dataproc-metastore/docs/release-notes",
    "Pub/Sub": "/pubsub/docs/release-notes",
    "Pub/Sub Lite": "/pubsub/lite/docs/release-notes",
    "Cloud Data Fusion": "/data-fusion/docs/release-notes",
    "Cloud Composer": "/composer/docs/release-notes",
    "Data Catalog": "/data-catalog/docs/release-notes",
    "Looker": "/looker/docs/release-notes",
    "Google Cloud Managed Service for Apache Kafka": "/managed-service-for-apache-kafka/docs/release-notes",
    # AI & ML
    "Vertex AI": "/vertex-ai/docs/release-notes",
    "Generative AI on Vertex AI": "/vertex-ai/generative-ai/docs/release-notes",
    "Vertex AI Search": "/generative-ai-app-builder/docs/release-notes",
    "Colab Enterprise": "/colab/docs/release-notes",
    "Document AI": "/document-ai/docs/release-notes",
    "Speech-to-Text": "/speech-to-text/docs/release-notes",
    "Text-to-Speech": "/text-to-speech/docs/release-notes",
    "Cloud Translation": "/translate/docs/release-notes",
    "Cloud Vision": "/vision/docs/release-notes",
    "Cloud Natural Language API": "/natural-language/docs/release-notes",
    "Video Intelligence API": "/video-intelligence/docs/release-notes",
    "Dialogflow": "/dialogflow/docs/release-notes",
    "Gemini Code Assist": "/gemini/docs/codeassist/release-notes",
    "Gemini Cloud Assist": "/cloud-assist/release-notes",
    "Model Armor": "/security-command-center/docs/release-notes",
    # Networking
    "Virtual Private Cloud": "/vpc/docs/release-notes",
    "Cloud Load Balancing": "/load-balancing/docs/release-notes",
    "Cloud DNS": "/dns/docs/release-notes",
    "Cloud CDN": "/cdn/docs/release-notes",
    "Cloud NAT": "/nat/docs/release-notes",
    "Cloud Router": "/network-connectivity/docs/router/release-notes",
    "Cloud VPN": "/network-connectivity/docs/vpn/release-notes",
    "Cloud Interconnect": "/network-connectivity/docs/interconnect/release-notes",
    "Network Connectivity Center": "/network-connectivity/docs/release-notes",
    "Network Intelligence Center": "/network-intelligence-center/docs/release-notes",
    "Media CDN": "/media-cdn/docs/release-notes",
    "Cloud Service Mesh": "/service-mesh/docs/release-notes",
    "Service Directory": "/service-directory/docs/release-notes",
    # Security & identity
    "Identity and Access Management": "/iam/docs/release-notes",
    "Identity-Aware Proxy": "/iap/docs/release-notes",
    "Identity Platform": "/identity-platform/docs/release-notes",
    "Secret Manager": "/secret-manager/docs/release-notes",
    "Cloud Key Management Service": "/kms/docs/release-notes",
    "Certificate Manager": "/certificate-manager/docs/release-notes",
    "Certificate Authority Service": "/certificate-authority-service/docs/release-notes",
    "Security Command Center": "/security-command-center/docs/release-notes",
    "Sensitive Data Protection": "/sensitive-data-protection/docs/release-notes",
    "VPC Service Controls": "/vpc-service-controls/docs/release-notes",
    "Binary Authorization": "/binary-authorization/docs/release-notes",
    "Assured Workloads": "/assured-workloads/docs/release-notes",
    "Access Approval": "/assured-workloads/access-approval/docs/release-notes",
    "reCAPTCHA": "/recaptcha/docs/release-notes",
    "Secure Web Proxy": "/secure-web-proxy/docs/release-notes",
    "Cloud IDS": "/intrusion-detection-system/docs/release-notes",
    "Cloud NGFW": "/firewall/docs/release-notes",
    "Chrome Enterprise Premium": "/beyondcorp-enterprise/docs/release-notes",
    "Google SecOps": "/chronicle/docs/release-notes",
    # DevOps, observability & management
    "Cloud Build": "/build/docs/release-notes",
    "Cloud Deploy": "/deploy/docs/release-notes",
    "Artifact Registry": "/artifact-registry/docs/release-notes",
    "Cloud Logging": "/logging/docs/release-notes",
    "Cloud Monitoring": "/monitoring/docs/release-notes",
    "Cloud Trace": "/trace/docs/release-notes",
    "Cloud Profiler": "/profiler/docs/release-notes",
    "Error Reporting": "/error-reporting/docs/release-notes",
    "Service Health": "/service-health/docs/release-notes",
    "Cloud Billing": "/billing/docs/release-notes",
    "Cloud Quotas": "/docs/quotas/release-notes",
    "Resource Manager": "/resource-manager/docs/release-notes",
    "Cloud Asset Inventory": "/asset-inventory/docs/release-notes",
    "Recommender": "/recommender/docs/release-notes",
    "Policy Intelligence": "/policy-intelligence/docs/release-notes",
    "Cloud Shell": "/shell/docs/release-notes",
    "Cloud SDK": "/sdk/docs/release-notes",
    "Cloud Deployment Manager": "/deployment-manager/docs/release-notes",
    "Infrastructure Manager": "/infrastructure-manager/docs/release-notes",
    "Config Connector": "/config-connector/docs/release-notes",
    "Secure Source Manager": "/secure-source-manager/docs/release-notes",
    "Developer Connect": "/developer-connect/docs/release-notes",
    "Cloud Source Repositories": "/source-repositories/docs/release-notes",
    # Application integration & serverless
    "Eventarc": "/eventarc/docs/release-notes",
    "Workflows": "/workflows/docs/release-notes",
    "Cloud Tasks": "/tasks/docs/release-notes",
    "Cloud Scheduler": "/scheduler/docs/release-notes",
    "Application Integration": "/application-integration/docs/release-notes",
    "Integration Connectors": "/integration-connectors/docs/release-notes",
    "API Gateway": "/api-gateway/docs/release-notes",
    "Cloud Endpoints": "/endpoints/docs/release-notes",
    "Apigee X": "/apigee/docs/release-notes",
    "Apigee hybrid": "/apigee/docs/hybrid/release-notes",
    # Migration
    "Migration Center": "/migration-center/docs/release-notes",
    "Migrate to Virtual Machines": "/migrate/virtual-machines/docs/release-notes",
    "Migrate to Containers": "/migrate/containers/docs/release-notes",
    # Media
    "Transcoder API": "/transcoder/docs/release-notes",
    "Live Stream API": "/livestream/docs/release-notes",
    "Video Stitcher API": "/video-stitcher/docs/release-notes",
    # Healthcare & industry
    "Cloud Healthcare API": "/healthcare-api/docs/release-notes",
}

# product name -> full URL, filled in lazily by the data store lookup so we only
# pay for a given product once per process.
_resolved_cache: Dict[str, str] = {}

_RELEASE_NOTES_PATH = re.compile(r"/release-notes(-archive)?/?$")


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


_NORMALIZED_PATHS = {_normalize(k): v for k, v in DOCS_PATHS.items()}


def date_anchor(published: _dt.date) -> str:
    """`date(2026, 7, 9)` -> `July_09_2026`, matching the devsite heading anchor."""
    return published.strftime("%B_%d_%Y")


def _from_map(product: str) -> Optional[str]:
    path = DOCS_PATHS.get(product) or _NORMALIZED_PATHS.get(_normalize(product))
    return f"{DOCS_BASE}{path}" if path else None


def _from_data_store(product: str) -> Optional[str]:
    """Ask the docs data store where this product's release notes live.

    Imported lazily so this module stays importable (and unit-testable) without
    Google Cloud credentials present.
    """
    try:
        from app.tools import _search_google_docs_datastore
    except Exception:  # pragma: no cover - only in envs without the deps
        return None

    try:
        results = _search_google_docs_datastore(
            query=f"{product} release notes", limit=5
        )
    except Exception as error:
        print(f"release-notes URL lookup failed for {product!r}: {error}")
        return None

    for result in results:
        url = (result.get("source_url") or "").strip()
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.netloc.endswith("cloud.google.com") and _RELEASE_NOTES_PATH.search(
            parsed.path
        ):
            return f"https://{parsed.netloc}{parsed.path}"
    return None


def resolve_page_url(product: str, *, use_data_store: bool = True) -> str:
    """The release-notes page for `product`, without a date anchor."""
    if not product:
        return ALL_PRODUCTS_URL

    if product in _resolved_cache:
        return _resolved_cache[product]

    url = _from_map(product)
    if url is None and use_data_store:
        url = _from_data_store(product)

    resolved = url or ALL_PRODUCTS_URL
    _resolved_cache[product] = resolved
    return resolved


def build_note_url(
    product: str, published: Optional[_dt.date], *, use_data_store: bool = True
) -> str:
    """The deep link for one release note: product page + date anchor."""
    page = resolve_page_url(product, use_data_store=use_data_store)
    if published is None:
        return page
    return f"{page}#{date_anchor(published)}"