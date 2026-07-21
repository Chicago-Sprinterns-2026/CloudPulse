import { useEffect, useState } from 'react';
import { loadRecentReleases, loadProductHistory, loadManifest } from './releaseNotesData';


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
