// Fetches the small, prebuilt files in /public/release-data instead of
// processing the ~21MB of raw source data in the browser. Those raw files
// live in /data-raw at the project root and are merged/deduped/split ONCE
// by `npm run build:data` (scripts/build-release-data.mjs) — re-run that
// any time a file is added to or changed in /data-raw.
//
//   recent.json           — last 12 months, every product (~3MB, one fetch)
//   manifest.json         — [{ product, slug, count }] for every product (~20KB)
//   by-product/<slug>.json — one product's FULL history, fetched on demand

const BASE = '/release-data';

let recentCache = null;
let recentPromise = null;

export function loadRecentReleases() {
  if (recentCache) return Promise.resolve(recentCache);
  if (recentPromise) return recentPromise;

  recentPromise = fetch(`${BASE}/recent.json`)
    .then((res) => {
      if (!res.ok) throw new Error(`recent.json fetch failed: ${res.status}`);
      return res.json();
    })
    .then((data) => {
      recentCache = data;
      recentPromise = null;
      return data;
    })
    .catch((err) => {
      recentPromise = null;
      throw err;
    });

  return recentPromise;
}

let manifestCache = null;
let manifestPromise = null;

export function loadManifest() {
  if (manifestCache) return Promise.resolve(manifestCache);
  if (manifestPromise) return manifestPromise;

  manifestPromise = fetch(`${BASE}/manifest.json`)
    .then((res) => {
      if (!res.ok) throw new Error(`manifest.json fetch failed: ${res.status}`);
      return res.json();
    })
    .then((data) => {
      manifestCache = data;
      manifestPromise = null;
      return data;
    })
    .catch((err) => {
      manifestPromise = null;
      throw err;
    });

  return manifestPromise;
}

const productHistoryCache = new Map();

// Product names in the app don't always exactly match the manifest's
// (same fuzzy-match issue as everywhere else — e.g. "Cloud SQL" vs
// "Cloud SQL for MySQL"). Exact match first, fall back to substring.
function findManifestEntry(manifest, product) {
  const exact = manifest.find((m) => m.product === product);
  if (exact) return exact;
  const lowerProduct = product.toLowerCase();
  return manifest.find(
    (m) => m.product.toLowerCase().includes(lowerProduct) || lowerProduct.includes(m.product.toLowerCase())
  );
}

export async function loadProductHistory(product) {
  if (productHistoryCache.has(product)) return productHistoryCache.get(product);

  const manifest = await loadManifest();
  const entry = findManifestEntry(manifest, product);
  if (!entry) {
    productHistoryCache.set(product, []);
    return [];
  }

  const res = await fetch(`${BASE}/by-product/${entry.slug}.json`);
  if (!res.ok) throw new Error(`${entry.slug}.json fetch failed: ${res.status}`);
  const data = await res.json();
  productHistoryCache.set(product, data);
  return data;
}
