import React from 'react';
import releaseData from './release_notes.json';


export default function Catalog({ onSelectProduct }) {
  const releases = releaseData.releases || [];

  return (
    <div className="catalog-view">
      <h3> 📅 July Cycle - Recent Updates</h3>
      <p className="subtitle">Select a product below to trigger the RAG synthesis engine.</p>
      
     <div className="catalog-grid">
        {/* Slice the latest 6 updates just like the Streamlit python setup did */}
        {releases.slice(0, 6).map((item, idx) => (
          <div key={idx} className="catalog-card">
            <h3 style={{ color: '#1a73e8' }}>{item.product}</h3>
            <small style={{ color: 'gray' }}>{item.date}</small>
            <p className="tag-description">
              {/* Grab the first 130 characters for the summary preview */}
              {item.update.substring(0, 130)}...
            </p>
            <button 
              className="btn btn-primary" 
              onClick={() => onSelectProduct(item.product)}
            >
              Synthesize {item.product}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}