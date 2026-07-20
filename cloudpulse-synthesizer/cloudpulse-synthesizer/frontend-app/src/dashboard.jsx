import React from 'react';
import releaseData from './release_notes.json';
import { stripHtml, truncate } from './utils';

export default function Dashboard({ onSelectProduct }) {
  const releases = releaseData.releases || [];

  return (
    <div className="catalog-view">
      <h3> 📅 Recent Updates</h3>
      <p className="subtitle">Select a product below to trigger the RAG synthesis engine.</p>

     <div className="catalog-grid">
        {/* Slice the latest 6 updates just like the Streamlit python setup did */}
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
