import React, { useEffect, useMemo, useState } from 'react';
import { useProductHistory } from './useReleaseNotes';
import { stripHtml } from './utils';

const PAGE_SIZE = 15;

export default function ReleaseHistory({ product, onBack, backLabel }) {
  const { releases: history, loading, error } = useProductHistory(product);

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);

  // Reset filters and pagination whenever the product changes.
  useEffect(() => {
    setDateFrom('');
    setDateTo('');
    setPage(1);
  }, [product]);

  const filtered = useMemo(() => {
    return history.filter((item) => {
      if (dateFrom && item.date < dateFrom) return false;
      if (dateTo && item.date > dateTo) return false;
      return true;
    });
  }, [history, dateFrom, dateTo]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const hasFilters = Boolean(dateFrom || dateTo);

  return (
    <div className="history-view">
      <button className="history-back" onClick={onBack}>{backLabel || '← Back'}</button>

      <h3>Full release history — {product}</h3>
      <p className="subtitle">
        {loading
          ? 'Loading full history…'
          : `${filtered.length} release${filtered.length === 1 ? '' : 's'} found${hasFilters ? ' (filtered)' : ''}.`}
      </p>

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
                setPage(1);
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
                setPage(1);
              }}
            />
          </div>
          {hasFilters && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setDateFrom('');
                setDateTo('');
                setPage(1);
              }}
            >
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
        {pageItems.map((item, idx) => (
          <div key={idx} className="history-item">
            <div className="history-item-meta">
              <span className="history-item-date">{item.date}</span>
              {item.type && <span className="history-item-type">{item.type}</span>}
            </div>
            <p>{stripHtml(item.update)}</p>
          </div>
        ))}
      </div>

      {!loading && filtered.length > PAGE_SIZE && (
        <div className="history-pagination">
          <button
            className="btn btn-secondary"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Previous
          </button>
          <span className="history-pagination-label">Page {page} of {totalPages}</span>
          <button
            className="btn btn-secondary"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
