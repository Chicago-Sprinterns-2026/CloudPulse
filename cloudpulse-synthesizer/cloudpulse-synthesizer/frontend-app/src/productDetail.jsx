import React, { useState } from 'react';
import ReleaseHistory from './releaseHistory';
import { GCP_PRODUCTS } from './products';
import { productsMatch } from './utils';
import ReactMarkdown from 'react-markdown';
import PRODUCT_DOCS from './data/productDocs.json';

export default function ProductDetail({ product, onBack, backLabel = '← Back to all products' }) {
  const [activeTab, setActiveTab] = useState('documentation');

  const catalogEntry =
    GCP_PRODUCTS.find((p) => p.name === product) ||
    GCP_PRODUCTS.find((p) => productsMatch(p.name, product)) ||
    null;

  const docContent = PRODUCT_DOCS[product] || null;

  return (
    <div className="product-detail-view">
      <div className="product-detail-topbar">
        <button className="history-back" onClick={onBack}>{backLabel}</button>
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
          {docContent ? (
            <div className="synthesis-output">
              <ReactMarkdown>{docContent}</ReactMarkdown>
            </div>
          ) : (
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