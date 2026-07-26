import api from './api';

// Release notes now come from the backend, which reads Google Cloud's public
// BigQuery release-notes dataset on every request. The old version of this file
// fetched /release-data/*.json — a build-time dump of the Cloud Storage bucket,
// which meant the ledger showed whatever was true the day someone last ran
// scripts/build-release-data.mjs. Those files (and that script) can go.

const PRODUCTS_PATH = '/api/release-notes/products';
const FEED_PATH = '/api/release-notes';

/**
 * One page of release notes, newest first.
 *
 * @param {object}  opts
 * @param {string}  [opts.product]  Substring match on product name. Omit for all products.
 * @param {string}  [opts.noteType] Exact type filter, e.g. 'BREAKING'.
 * @param {string}  [opts.cursor]   next_cursor from a previous call.
 * @param {number}  [opts.limit]
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<{items: Array, nextCursor: string|null, hasMore: boolean, fetchedAt: string}>}
 */
export async function fetchReleaseNotes({
  product,
  noteType,
  cursor,
  limit = 20,
  signal,
} = {}) {
  const params = { limit };
  if (product) params.product = product;
  if (noteType) params.note_type = noteType;
  if (cursor) params.cursor = cursor;

  const { data } = await api.get(FEED_PATH, { params, signal });

  return {
    items: data.items || [],
    nextCursor: data.next_cursor || null,
    hasMore: Boolean(data.has_more),
    fetchedAt: data.fetched_at,
    // False when the backend is serving the offline fixture rather than BigQuery.
    isLive: data.is_live !== false,
    source: data.source || 'unknown',
  };
}

// The product list changes on the order of weeks, so one fetch per page load is
// plenty. Cached as a promise, not a value, so concurrent callers during startup
// share a single request instead of racing.
let productsPromise = null;

/**
 * Every product with release notes, most active first:
 * [{ product, count, latest_date }]
 */
export function loadProducts() {
  if (!productsPromise) {
    productsPromise = api
      .get(PRODUCTS_PATH)
      .then(({ data }) => data.products || [])
      .catch((err) => {
        productsPromise = null; // let the next caller retry
        throw err;
      });
  }
  return productsPromise;
}

/**
 * Pulls a product's entire history by walking the cursor to the end.
 *
 * Used by the standalone release-history view, which paginates and date-filters
 * client side. The workspace ledger does not use this — it scrolls page by page
 * so it never has to wait on a product with thousands of notes.
 */
export async function loadProductHistory(product, { maxPages = 40, pageSize = 100 } = {}) {
  if (!product) return [];

  const all = [];
  let cursor = null;

  for (let page = 0; page < maxPages; page += 1) {
    // eslint-disable-next-line no-await-in-loop
    const { items, nextCursor } = await fetchReleaseNotes({
      product,
      cursor,
      limit: pageSize,
    });
    all.push(...items);
    if (!nextCursor) break;
    cursor = nextCursor;
  }

  return all;
}