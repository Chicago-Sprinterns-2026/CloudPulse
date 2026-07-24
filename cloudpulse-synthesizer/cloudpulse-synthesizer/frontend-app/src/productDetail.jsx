import React, { useState, useEffect } from 'react';
import ReleaseHistory from './releaseHistory';
import { GCP_PRODUCTS } from './products';
import { productsMatch } from './utils';
import api from './api';
import ReactMarkdown from 'react-markdown';

export default function ProductDetail({ product, onBack }) {
  const [activeTab, setActiveTab] = useState('documentation');
  const [docContent, setDocContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (activeTab !== 'documentation' || !product) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    api.get(`/api/products/summary?product_name=${encodeURIComponent(product)}`)
      .then((res) => {
        if (!cancelled) {
          setDocContent(res.data.summary);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [product, activeTab]);

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
          {loading && <p className="subtitle">Loading documentation…</p>}
          {error && (
            <p className="subtitle" style={{ color: 'var(--coral)' }}>
              Couldn't load documentation: {error.message}
            </p>
          )}
          {!loading && !error && docContent ? (
            <div className="synthesis-output">
              <ReactMarkdown>{docContent}</ReactMarkdown>
            </div>
          ) : !loading && !error && (
            <div className="product-doc-placeholder">
              📄 Documentation for {product} will appear here once it's connected to the backend data store.
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <ReleaseHistory product={product} embedded />
      )}
    </div>
  );
}