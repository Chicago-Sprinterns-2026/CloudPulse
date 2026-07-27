import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useProductHistory } from './useReleaseNotes';

// How many notes to show initially, and how many more each time the reader
// reaches the bottom. The full history is already in memory (see
// loadProductHistory), so this is purely about not rendering 600 DOM nodes at
// once -- and about keeping date filtering instant, which server-side paging
// would not.
const PAGE_SIZE = 20;

export default function ReleaseHistory({ product, onBack, backLabel, embedded = false }) {
  const { releases: history, loading, error, isLive } = useProductHistory(product);

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [visible, setVisible] = useState(PAGE_SIZE);

  // Reset filters and the scroll window whenever the product changes.
  useEffect(() => {
    setDateFrom('');
    setDateTo('');
    setVisible(PAGE_SIZE);
  }, [product]);

  const filtered = useMemo(() => {
    return history.filter((item) => {
      if (dateFrom && item.date < dateFrom) return false;
      if (dateTo && item.date > dateTo) return false;
      return true;
    });
  }, [history, dateFrom, dateTo]);

  const pageItems = filtered.slice(0, visible);
  const hasMore = visible < filtered.length;
  const hasFilters = Boolean(dateFrom || dateTo);

  // Infinite scroll: a sentinel below the last note reveals the next batch as
  // soon as it enters the viewport. Replaces the old numbered pager -- reading
  // release notes is a scanning task, and page buttons interrupt it.
  const sentinelRef = useRef(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasMore) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible((current) => current + PAGE_SIZE);
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, pageItems.length]);

  const resetFilters = () => {
    setDateFrom('');
    setDateTo('');
    setVisible(PAGE_SIZE);
  };

  return (
    <div className="history-view">
      {!embedded && (
        <>
          <button className="history-back" onClick={onBack}>{backLabel || '← Back'}</button>
          <h3>Full release history — {product}</h3>
        </>
      )}

      <div className="history-status">
        <p className="subtitle">
          {loading
            ? 'Loading full history…'
            : `${filtered.length} release${filtered.length === 1 ? '' : 's'} found${hasFilters ? ' (filtered)' : ''}.`}
        </p>
        {!loading && !error && history.length > 0 && (
          <p className={`note history-source${isLive ? '' : ' history-stale'}`}>
            {isLive
              ? 'Live from Google Cloud · click any note to open it in the docs'
              : 'Offline snapshot · click any note to open it in the docs'}
          </p>
        )}
      </div>

      {error && (
        <p className="subtitle" style={{ color: 'var(--coral)' }}>
          Couldn't load history: {error.message}
        </p>
      )}

      {!loading && history.length > 0 && (
        <div className="history-filters">
          <div className="input-group">
            <label>From</label>
            <input
              type="date"
              value={dateFrom}
              max={dateTo || undefined}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setVisible(PAGE_SIZE);
              }}
            />
          </div>
          <div className="input-group">
            <label>To</label>
            <input
              type="date"
              value={dateTo}
              min={dateFrom || undefined}
              onChange={(e) => {
                setDateTo(e.target.value);
                setVisible(PAGE_SIZE);
              }}
            />
          </div>
          {hasFilters && (
            <button className="btn btn-secondary" onClick={resetFilters}>
              Clear filters
            </button>
          )}
        </div>
      )}

      <div className="history-list">
        {!loading && filtered.length === 0 && !error && (
          <p className="subtitle">
            {hasFilters
              ? `No release notes for "${product}" in the selected date range.`
              : `No release notes found for "${product}".`}
          </p>
        )}

        {pageItems.map((item) => (
          // Each note links to the exact date anchor on the official page, so a
          // reader can always get to the authoritative version of what they're
          // reading rather than trusting our copy of it.
          <a
            key={item.id}
            className="history-item"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            title={`Open the ${item.product} release notes for ${item.date}`}
          >
            <div className="history-item-meta">
              <span className="history-item-date">{item.date}</span>
              {item.type && <span className="history-item-type">{item.type}</span>}
              {item.version && <span className="history-item-version">{item.version}</span>}
            </div>
            <p>{item.update}</p>
          </a>
        ))}

        {/* Watched by the IntersectionObserver above. */}
        <div ref={sentinelRef} className="history-sentinel" aria-hidden="true" />

        {!loading && !hasMore && filtered.length > PAGE_SIZE && (
          <p className="note history-end">
            That's the full history for {product}.
          </p>
        )}
      </div>
    </div>
  );
}