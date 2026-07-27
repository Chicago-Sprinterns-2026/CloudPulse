import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLiveReleaseNotes, useManifest } from './useReleaseNotes';
import { truncate } from './utils';
import Chatbot from './chatbot';

// Long enough that typing "compute engine" is one request, not thirteen.
const FILTER_DEBOUNCE_MS = 350;
const PAGE_SIZE = 20;

export default function Synthesizer({ defaultProduct, onViewHistory }) {
  const [productName, setProductName] = useState(defaultProduct || '');
  const [productFilter, setProductFilter] = useState((defaultProduct || '').trim());

  // The input updates on every keystroke; the query the server sees lags behind it.
  useEffect(() => {
    const timer = setTimeout(() => setProductFilter(productName.trim()), FILTER_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [productName]);

  const {
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
  } = useLiveReleaseNotes({ product: productFilter, pageSize: PAGE_SIZE });

  const { manifest } = useManifest();

  // The feed filters with SQL LIKE '%query%', which can span several products
  // ("Compute Engine" also matches "Compute Engine Guest environment"). Summing
  // every match keeps this number honest against what the list actually returns.
  const totalCount = useMemo(() => {
    if (!productFilter) return 0;
    const needle = productFilter.toLowerCase();
    return manifest
      .filter((m) => m.product.toLowerCase().includes(needle))
      .reduce((sum, m) => sum + m.count, 0);
  }, [manifest, productFilter]);

  // Infinite scroll: a sentinel at the bottom of the scroll container asks for
  // the next page as soon as it comes into view. `root` is the ledger itself, not
  // the viewport, because the ledger is its own scroll area.
  const sentinelRef = useRef(null);
  const scrollRef = useRef(null);
  const loadMoreRef = useRef(loadMore);
  loadMoreRef.current = loadMore;

  useEffect(() => {
    const sentinel = sentinelRef.current;
    const root = scrollRef.current;
    if (!sentinel || !root || !hasMore) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) loadMoreRef.current();
      },
      { root, rootMargin: '120px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, items.length]);

  const jumpToNewest = () => {
    acknowledgeNew();
    if (scrollRef.current) scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="workspace-grid">
      {/* Left: full chatbot — Q&A and one-pager generation in one thread */}
      <div className="form-panel chat-panel">
        <Chatbot product={productFilter} manifest={manifest} />
      </div>

      {/* Right: live release notes ledger */}
      <div className="ledger-panel">
        <h4>Release Notes Ledger</h4>

        <div className="input-group">
          <label>Google Cloud product</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="e.g. Compute Engine, Vertex AI"
          />
        </div>

        <div className="ledger-status">
          <p className="subtitle">
            {productFilter
              ? `${productFilter}${totalCount ? ` · ${totalCount} notes` : ''}`
              : 'All products'}
            {loading && ' · loading…'}
          </p>
          {lastUpdated && !loading && (
            <p className={`note ledger-timestamp${isLive ? '' : ' ledger-stale'}`}>
              {isLive ? 'Live from Google Cloud · checked ' : 'Offline snapshot · loaded '}
              {new Date(lastUpdated).toLocaleTimeString([], {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>

        {newCount > 0 && (
          <button type="button" className="ledger-new-badge" onClick={jumpToNewest}>
            ↑ {newCount} new {newCount === 1 ? 'note' : 'notes'}
          </button>
        )}

        {error && (
          <p className="subtitle" style={{ color: 'var(--coral)' }}>
            Couldn't reach the release notes feed: {error.message}
          </p>
        )}

        <div className="scrolling-ledger" ref={scrollRef}>
          {!loading && items.length === 0 && !error && (
            <p className="note">
              {productFilter
                ? `No release notes found for "${productFilter}".`
                : 'No release notes found.'}
            </p>
          )}

          {items.map((item) => (
            <a
              key={item.id}
              className="ledger-item"
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              title={`Open the ${item.product} release notes for ${item.date}`}
            >
              <p>
                🔹 <strong>{item.product}</strong>{' '}
                <span className="note">{item.date}</span>
                {item.type && <span className="ledger-item-type">{item.type}</span>}
              </p>
              <p className="note">{truncate(item.update, 160)}</p>
            </a>
          ))}

          {/* Watched by the IntersectionObserver above. */}
          <div ref={sentinelRef} className="ledger-sentinel" aria-hidden="true" />

          {loadingMore && <p className="note ledger-loading">Loading older notes…</p>}

          {!loading && !hasMore && items.length > 0 && (
            <p className="note ledger-end">
              That's the full history{productFilter ? ` for ${productFilter}` : ''}.
            </p>
          )}
        </div>

        {productFilter && onViewHistory && (
          <button
            type="button"
            className="btn btn-secondary full-width"
            style={{ marginTop: '12px' }}
            onClick={() => onViewHistory(productFilter)}
          >
            Browse {productFilter} history by date
          </button>
        )}
      </div>
    </div>
  );
}