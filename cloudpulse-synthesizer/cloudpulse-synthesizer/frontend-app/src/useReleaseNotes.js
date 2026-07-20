import { useEffect, useState } from 'react';
import { loadRecentReleases, loadProductHistory, loadManifest } from './releaseNotesData';

// Returns { releases, loading, error } for the last 12 months, across every
// product. Backed by a single ~3MB fetch of the prebuilt recent.json
// (see releaseNotesData.js) instead of processing all raw source files.
export function useReleaseNotes() {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadRecentReleases()
      .then((data) => {
        if (!cancelled) {
          setReleases(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { releases, loading, error };
}

// Returns { releases, loading, error } for ONE product's full history
// (all dates, not just the last 12 months). Fetches only that product's
// small prebuilt file — not the full dataset. `product` may be null/empty
// while a selection hasn't been made yet; the hook just stays idle.
export function useProductHistory(product) {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(Boolean(product));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!product) {
      setReleases([]);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    loadProductHistory(product)
      .then((data) => {
        if (!cancelled) {
          setReleases(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [product]);

  return { releases, loading, error };
}

// Returns { manifest, loading } — the small [{ product, slug, count }] list
// covering every product's TOTAL release count (not just last-12-months),
// used to decide whether a "show full history" link is worth showing.
export function useManifest() {
  const [manifest, setManifest] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    loadManifest()
      .then((data) => {
        if (!cancelled) {
          setManifest(data);
          setLoading(false);
        }
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
