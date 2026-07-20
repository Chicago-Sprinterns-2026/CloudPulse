import React from 'react';
import { useProductHistory } from './useReleaseNotes';
import { stripHtml } from './utils';

export default function ReleaseHistory({ product, onBack }) {
  const { releases: history, loading, error } = useProductHistory(product);

  return (
    <div className="history-view">
      <button className="history-back" onClick={onBack}>← Back to workspace</button>

      <h3>Full release history — {product}</h3>
      <p className="subtitle">
        {loading
          ? 'Loading full history…'
          : `${history.length} release${history.length === 1 ? '' : 's'} found.`}
      </p>

      {error && (
        <p className="subtitle" style={{ color: 'var(--coral)' }}>
          Couldn't load history: {error.message}
        </p>
      )}

      <div className="history-list">
        {!loading && history.length === 0 && !error && (
          <p className="subtitle">No release notes found for "{product}".</p>
        )}
        {history.map((item, idx) => (
          <div key={idx} className="history-item">
            <div className="history-item-meta">
              <span className="history-item-date">{item.date}</span>
              {item.type && <span className="history-item-type">{item.type}</span>}
            </div>
            <p>{stripHtml(item.update)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
