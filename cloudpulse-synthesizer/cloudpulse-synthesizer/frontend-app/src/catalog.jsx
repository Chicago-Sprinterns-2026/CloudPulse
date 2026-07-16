import React from 'react';

const PRODUCTS = [
  { id: 'compute', name: 'Compute Engine', tag: 'Virtual machines, resized on demand', icon: '⚙️', meta: 'updated this cycle' },
  { id: 'vertex', name: 'Vertex AI', tag: 'Train, tune, and serve models', icon: '✦', meta: 'updated this cycle' },
  { id: 'cloudsql', name: 'Cloud SQL', tag: 'Managed relational databases', icon: '⚃', meta: 'updated this cycle' }
];

export default function Catalog({ onSelectProduct }) {
  return (
    <div className="catalog-view">
      <h3>Product Catalog</h3>
      <p className="subtitle">Select a product below to view active release notes.</p>
      
      <div className="catalog-grid">
        {PRODUCTS.map((p) => (
          <div key={p.id} className="catalog-card">
            <h3>{p.icon} {p.name}</h3>
            <p className="tag"><em>{p.tag}</em></p>
            <p className="meta">🔴 <strong>{p.meta}</strong></p>
            <button 
              className="btn btn-primary" 
              onClick={() => onSelectProduct(p.name)}
            >
              View {p.name} Notes
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}