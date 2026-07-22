import React, { useState } from 'react';
import ReleaseHistory from './releaseHistory';
import { GCP_PRODUCTS } from './products';
import { productsMatch } from './utils';

export default function ProductDetail({ product, onBack }) {
  const [activeTab, setActiveTab] = useState('documentation');

  const catalogEntry =
    GCP_PRODUCTS.find((p) => p.name === product) ||
    GCP_PRODUCTS.find((p) => productsMatch(p.name, product)) ||
    null;

  return (
    <div className="product-detail-view">
      <div className="product-detail-topbar">
        <button className="history-back" onClick={onBack}>← Back to all products</button>
      </div>

      <div className="product-detail-header">
        <h3>{product}</h3>
        {catalogEntry && (
          <p className="subtitle">{catalogEntry.category} — {catalogEntry.description}</p>
        )}
      </div>

      <div className="browse-tabs">
        <button
          className={`browse-tab ${activeTab === 'documentation' ? 'active' : ''}`}
          onClick={() => setActiveTab('documentation')}
        >
          Documentation
        </button>
        <button
          className={`browse-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          Release History
        </button>
      </div>

      {activeTab === 'documentation' && (
        <div className="product-doc-panel">
          {/* PLACEHOLDER: no backend data store wired up yet. Once one
              exists, replace this with a fetch (same pattern as
              useReleaseNotes.js) rather than inventing a contract here
              ahead of what the backend team actually builds. */}
          <div className="product-doc-placeholder">
            📄 Documentation for {product} will appear here once it's connected to the backend data store.
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <ReleaseHistory product={product} embedded />
      )}
    </div>
  );
}
