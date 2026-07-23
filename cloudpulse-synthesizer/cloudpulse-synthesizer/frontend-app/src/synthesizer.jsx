import React, { useMemo, useState } from 'react';
import { useReleaseNotes, useManifest } from './useReleaseNotes';
import { productsMatch } from './utils';
import Chatbot from './chatbot';

const RECENT_COUNT = 6;

function matchesProduct(release, query) {
  return release.product.toLowerCase().includes(query.trim().toLowerCase());
}

export default function Synthesizer({ defaultProduct, onViewHistory }) {
  const [productName, setProductName] = useState(defaultProduct || '');

  // Already scoped to the last 12 months — see public/release-data/recent.json
  // and scripts/build-release-data.mjs.
  const { releases: RECENT_RELEASES, loading } = useReleaseNotes();
  const { manifest } = useManifest();

  const matchingReleases = useMemo(
    () => (productName.trim() ? RECENT_RELEASES.filter((r) => matchesProduct(r, productName)) : []),
    [productName, RECENT_RELEASES]
  );

  const ledgerItems = productName.trim() ? matchingReleases : RECENT_RELEASES.slice(0, RECENT_COUNT);

  // Total history for the typed product
  const totalCount = useMemo(() => {
    if (!productName.trim()) return 0;
    const entry = manifest.find((m) => productsMatch(m.product, productName));
    return entry ? entry.count : 0;
  }, [manifest, productName]);

  const hasOlderHistory = productName.trim() && totalCount > matchingReleases.length;

  return (
    <div className="workspace-grid">
      {/* Left: full chatbot — Q&A and one-pager generation in one thread */}
      <div className="form-panel chat-panel">
        <Chatbot product={productName.trim()} />
      </div>

      {/* Right: release notes ledger */}
      <div className="ledger-panel">
        <h4>Release Notes Ledger</h4>

        <div className="input-group">
          <label>Google Cloud product</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="e.g. Compute Engine, Vertex AI"
          />
        </div>

        <p className="subtitle" style={{ marginBottom: '10px' }}>
          Last 12 months{loading && ' · loading…'}
        </p>
        <div className="scrolling-ledger">
          {ledgerItems.length === 0 && !loading && (
            <p className="note">
              {productName.trim()
                ? `No release notes in the last 12 months for "${productName}".`
                : 'No recent release notes found.'}
            </p>
          )}
          {ledgerItems.map((item, idx) => (
            <div
              key={idx}
              className="ledger-item"
              role="button"
              tabIndex={0}
              onClick={() => setProductName(item.product)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setProductName(item.product)}
            >
              <p>🔹 <strong>{item.product}</strong> <span className="note">{item.date}</span></p>
              <p className="note">{item.update.slice(0, 130)}...</p>
              {idx < ledgerItems.length - 1 && <hr />}
            </div>
          ))}

          {hasOlderHistory && (
            <button
              className="btn btn-secondary full-width"
              style={{ marginTop: '12px' }}
              onClick={() => onViewHistory && onViewHistory(productName.trim())}
            >
              Show full history for {productName.trim()} ({totalCount} total)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
