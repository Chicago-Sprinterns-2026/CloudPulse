import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchReleaseNotes, loadProducts, loadProductHistory } from './releaseNotesData';

const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_POLL_MS = 60_000; // matches the backend's 60s cache on the first page

/**
 * Live, endlessly-scrollable release notes.
 *
 * Two jobs:
 *   - loadMore() walks backwards through history via the server's cursor, so a
 *     user can scroll as far into the past as they want without ever loading the
 *     whole dataset.
 *   - a poll re-fetches page one on an interval and prepends anything new, so
 *     the ledger keeps up with Google Cloud without a page refresh.
 *
 * @param {object}  opts
 * @param {string}  [opts.product]   Product filter; changing it resets the feed.
 * @param {string}  [opts.noteType]  Type filter, e.g. 'BREAKING'.
 * @param {number}  [opts.pageSize]
 * @param {number}  [opts.pollMs]    0 disables polling.
 */
export function useLiveReleaseNotes({
  product = '',
  noteType = '',
  pageSize = DEFAULT_PAGE_SIZE,
  pollMs = DEFAULT_POLL_MS,
} = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [newCount, setNewCount] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  // Whether the backend is serving BigQuery or the offline fixture.
  const [isLive, setIsLive] = useState(true);

  const cursorRef = useRef(null);
  // Bumped on every filter change. Any in-flight response carrying a stale
  // generation is discarded, which is what stops a slow first-page request from
  // landing after the user has already typed a different product.
  const generationRef = useRef(0);
  const seenIdsRef = useRef(new Set());

  // ---- first page (and reset on filter change) ---------------------------- //
  useEffect(() => {
    const generation = generationRef.current + 1;
    generationRef.current = generation;

    const controller = new AbortController();

    setLoading(true);
    setError(null);
    setItems([]);
    setHasMore(false);
    setNewCount(0);
    cursorRef.current = null;
    seenIdsRef.current = new Set();

    fetchReleaseNotes({ product, noteType, limit: pageSize, signal: controller.signal })
      .then(({ items: page, nextCursor, hasMore: more, fetchedAt, isLive: live }) => {
        if (generationRef.current !== generation) return;
        seenIdsRef.current = new Set(page.map((item) => item.id));
        cursorRef.current = nextCursor;
        setItems(page);
        setHasMore(more);
        setLastUpdated(fetchedAt);
        setIsLive(live);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted || generationRef.current !== generation) return;
        setError(err);
        setLoading(false);
      });

    return () => controller.abort();
  }, [product, noteType, pageSize]);

  // ---- older pages ------------------------------------------------------- //
  const loadMore = useCallback(() => {
    if (loadingMore || loading || !cursorRef.current) return;

    const generation = generationRef.current;
    setLoadingMore(true);

    fetchReleaseNotes({ product, noteType, limit: pageSize, cursor: cursorRef.current })
      .then(({ items: page, nextCursor, hasMore: more }) => {
        if (generationRef.current !== generation) return;

        // The cursor makes duplicates unlikely, but a note published while the
        // user scrolls can still shift things — so filter defensively rather
        // than risk React key collisions.
        const fresh = page.filter((item) => !seenIdsRef.current.has(item.id));
        fresh.forEach((item) => seenIdsRef.current.add(item.id));

        cursorRef.current = nextCursor;
        setItems((prev) => [...prev, ...fresh]);
        setHasMore(more);
        setLoadingMore(false);
      })
      .catch((err) => {
        if (generationRef.current !== generation) return;
        setError(err);
        setLoadingMore(false);
      });
  }, [loading, loadingMore, noteType, pageSize, product]);

  // ---- polling for new notes --------------------------------------------- //
  useEffect(() => {
    if (!pollMs) return undefined;

    const interval = setInterval(() => {
      const generation = generationRef.current;

      fetchReleaseNotes({ product, noteType, limit: pageSize })
        .then(({ items: page, fetchedAt, isLive: live }) => {
          if (generationRef.current !== generation) return;

          const fresh = page.filter((item) => !seenIdsRef.current.has(item.id));
          setLastUpdated(fetchedAt);
          setIsLive(live);
          if (fresh.length === 0) return;

          fresh.forEach((item) => seenIdsRef.current.add(item.id));
          setItems((prev) => [...fresh, ...prev]);
          setNewCount((prev) => prev + fresh.length);
        })
        .catch(() => {
          // A failed poll is not worth surfacing — what's on screen is still
          // valid, and the next tick will try again.
        });
    }, pollMs);

    return () => clearInterval(interval);
  }, [noteType, pageSize, pollMs, product]);

  const acknowledgeNew = useCallback(() => setNewCount(0), []);

  return {
    items,
    loading,
    loadingMore,
    error,
    hasMore,
    loadMore,
    newCount,
    acknowledgeNew,
    lastUpdated,
    isLive,
  };
}

/**
 * The most recent notes across all products, as a plain array.
 *
 * Kept because catalog.jsx and dashboard.jsx already import this name and only
 * need the newest handful — they slice to 6 and 5 respectively. Backed by the
 * live feed now instead of recent.json, so those views update on their own too.
 * New code should prefer useLiveReleaseNotes, which paginates.
 */
export function useReleaseNotes({ limit = 25 } = {}) {
  const { items, loading, error } = useLiveReleaseNotes({ pageSize: limit });
  return { releases: items, loading, error };
}

/**
 * A product's full history in one array.
 *
 * Kept for releaseHistory.jsx, which filters and paginates client side. Same
 * signature as before, so that component needs no changes.
 */
export function useProductHistory(product) {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(Boolean(product));
  const [error, setError] = useState(null);
  // False when the backend is serving the offline fixture rather than BigQuery.
  const [isLive, setIsLive] = useState(true);

  useEffect(() => {
    if (!product) {
      setReleases([]);
      setLoading(false);
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    loadProductHistory(product)
      .then(({ items, isLive: live }) => {
        if (cancelled) return;
        setReleases(items);
        setIsLive(live);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [product]);

  return { releases, loading, error, isLive };
}

/**
 * Product list for typeaheads and totals: [{ product, count, latest_date }].
 *
 * Named `useManifest` still because callers already import it under that name;
 * it's now backed by /api/release-notes/products rather than manifest.json.
 */
export function useManifest() {
  const [manifest, setManifest] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    loadProducts()
      .then((data) => {
        if (cancelled) return;
        setManifest(data);
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { manifest, loading };
}