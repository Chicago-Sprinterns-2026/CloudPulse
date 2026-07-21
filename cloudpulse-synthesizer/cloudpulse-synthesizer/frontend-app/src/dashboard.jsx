import React, { useMemo } from 'react';
import { useReleaseNotes } from './useReleaseNotes';
import { GCP_PRODUCTS } from './products';
import { stripHtml, truncate, productsMatch } from './utils';

const BRAND_COLORS = ['var(--g-blue)', 'var(--g-red)', 'var(--g-yellow)', 'var(--g-green)'];

//Mock Data
const MOCK_USER_PRODUCTS = ['Compute Engine', 'Cloud SQL', 'BigQuery'];

export default function Dashboard({ onSelectProduct }) {
  const { releases, loading } = useReleaseNotes();

  const recentReleases = useMemo(() => {
    return releases
      .filter((r) => MOCK_USER_PRODUCTS.some((p) => productsMatch(r.product, p)))
      .slice(0, 3);
  }, [releases]);

  const recommended = useMemo(() => {
    const usedCategories = new Set(
      GCP_PRODUCTS.filter((p) => MOCK_USER_PRODUCTS.includes(p.name)).map((p) => p.category)
    );
    return GCP_PRODUCTS
      .filter((p) => usedCategories.has(p.category) && !MOCK_USER_PRODUCTS.includes(p.name))
      .slice(0, 4);
  }, []);

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h3>👋 Welcome back</h3>
        <p className="subtitle">
          Showing updates for the products on your account: {MOCK_USER_PRODUCTS.join(', ')}.
        </p>
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-panel">
          <h4>Your recent releases</h4>
          <p className="subtitle">Top updates across the products you already use.</p>

          <div className="dashboard-release-list">
            {loading && <p className="subtitle">Loading release notes…</p>}
            {!loading && recentReleases.length === 0 && (
              <p className="subtitle">No recent releases found for your products.</p>
            )}
            {!loading && recentReleases.map((item, idx) => {
              const summary = truncate(stripHtml(item.update), 110);
              return (
                <button
                  key={idx}
                  className="dashboard-release-card"
                  onClick={() => onSelectProduct(item.product)}
                >
                  <div className="dashboard-release-meta">
                    <span className="dashboard-release-product">{item.product}</span>
                    <span className="dashboard-release-date">{item.date}</span>
                  </div>
                  <p>{summary}</p>
                </button>
              );
            })}
          </div>
        </section>

        <section className="dashboard-panel">
          <h4>Recommended for you</h4>
          <p className="subtitle">Based on the categories you're already active in.</p>

          <div className="dashboard-recommend-list">
            {recommended.length === 0 && (
              <p className="subtitle">No recommendations available right now.</p>
            )}
            {recommended.map((product, i) => (
              <button
                key={product.name}
                className="dashboard-recommend-card"
                style={{ '--chip-color': BRAND_COLORS[i % 4] }}
                onClick={() => onSelectProduct(product.name)}
              >
                <span className="dashboard-recommend-dot" />
                <span className="dashboard-recommend-name">{product.name}</span>
                <span className="dashboard-recommend-category">{product.category}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
