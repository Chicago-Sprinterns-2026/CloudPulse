import React, { useMemo, useState } from 'react';
import { GCP_PRODUCTS, CATEGORIES } from './products';
import { PRODUCT_IMAGES, CATEGORY_ICONS } from './productImages';

const BRAND_COLORS = ['var(--g-blue)', 'var(--g-red)', 'var(--g-yellow)', 'var(--g-green)'];

export default function ProductDirectory({ onSeeMore }) {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  const filtered = useMemo(() => {
    return GCP_PRODUCTS.filter((p) => {
      const matchesCategory = activeCategory === 'All' || p.category === activeCategory;
      const matchesQuery = p.name.toLowerCase().includes(query.trim().toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [query, activeCategory]);

  return (
    <div className="directory-view">
      <h3>All Google Cloud products</h3>
      <p className="subtitle">Browse or filter by category, then select a product to view its documentation and release notes.</p>

      <div className="directory-controls">
        <input
          type="text"
          className="directory-search"
          placeholder="Search products..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <div className="category-chips">
          <button
            className={`category-chip ${activeCategory === 'All' ? 'active' : ''}`}
            onClick={() => setActiveCategory('All')}
          >
            All ({GCP_PRODUCTS.length})
          </button>
          {CATEGORIES.map((cat, i) => (
            <button
              key={cat}
              className={`category-chip ${activeCategory === cat ? 'active' : ''}`}
              style={{ '--chip-color': BRAND_COLORS[i % 4] }}
              onClick={() => setActiveCategory(cat)}
            >
              {CATEGORY_ICONS[cat] && (
                <img
                  src={CATEGORY_ICONS[cat]}
                  alt=""
                  className="category-chip-icon"
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              )}
              {cat}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="directory-empty">No products match "{query}".</p>
      ) : (
        <div className="directory-grid">
          {filtered.map((p) => {
            const colorIndex = CATEGORIES.indexOf(p.category) % 4;
            const imageSrc = PRODUCT_IMAGES[p.name] || CATEGORY_ICONS[p.category];
            return (
              <div
                key={p.name}
                className="directory-card"
                style={{ '--chip-color': BRAND_COLORS[colorIndex] }}
              >
                <button className="directory-card-main" onClick={() => onSeeMore(p.name)}>
                  {imageSrc ? (
                    <img
                      src={imageSrc}
                      alt={`${p.name} icon`}
                      className="directory-card-photo"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  ) : (
                    <span className="directory-card-dot" />
                  )}
                  <span className="directory-card-name">{p.name}</span>
                  <span className="directory-card-category">{p.category}</span>
                </button>
                <button className="directory-card-history-link" onClick={() => onSeeMore(p.name)}>
                  See more →
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
