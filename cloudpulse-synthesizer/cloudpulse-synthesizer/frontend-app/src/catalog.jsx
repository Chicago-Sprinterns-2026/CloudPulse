import React from 'react';
import { useReleaseNotes } from './useReleaseNotes';
import { stripHtml, truncate } from './utils';

export default function Catalog({ onSelectProduct }) {
  const { releases, loading, error } = useReleaseNotes();

  return (
    <div className="catalog-view">
      <h3> 📅 Recent Updates</h3>
      <p className="subtitle">Select a product below to trigger the RAG synthesis engine.</p>

      {loading && <p className="subtitle">Loading release notes…</p>}
      {error && <p className="subtitle" style={{ color: 'var(--coral)' }}>Couldn't load release notes: {error.message}</p>}

     <div className="catalog-grid">
        {/* Slice the latest 6 updates across every merged release notes file */}
        {releases.slice(0, 6).map((item, idx) => {
          const summary = truncate(stripHtml(item.update), 130);
          return (
            <div key={idx} className="catalog-card">
              <h3 style={{ color: '#1a73e8' }}>{item.product}</h3>
              <small style={{ color: 'gray' }}>{item.date}</small>
              <p className="tag-description">{summary}</p>
              <button 
                className="btn btn-primary" 
                onClick={() => onSelectProduct(item.product)}
              >
                Synthesize {item.product}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
