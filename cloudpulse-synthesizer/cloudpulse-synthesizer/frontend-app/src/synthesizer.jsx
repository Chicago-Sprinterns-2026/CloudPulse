import React, { useState, useMemo } from 'react';
import releaseData from './release_notes.json';

const ALL_RELEASES = releaseData.releases || [];
const RECENT_COUNT = 6;

function matchesProduct(release, query) {
  return release.product.toLowerCase().includes(query.trim().toLowerCase());
}

export default function Synthesizer({ defaultProduct }) {
  const [productName, setProductName] = useState(defaultProduct || '');
  const [output, setOutput] = useState('');

  const matchingReleases = useMemo(
    () => (productName.trim() ? ALL_RELEASES.filter((r) => matchesProduct(r, productName)) : []),
    [productName]
  );

  const ledgerItems = productName.trim() ? matchingReleases : ALL_RELEASES.slice(0, RECENT_COUNT);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!productName.trim()) return;

    if (matchingReleases.length === 0) {
      setOutput(`### MOCK SYNTHESIS ONE-PAGER\n**Product:** ${productName}\n\nNo release notes found for "${productName}" in the ledger.`);
      return;
    }

    const latest = matchingReleases[0];
    setOutput(`### MOCK SYNTHESIS ONE-PAGER\n**Product:** ${latest.product}\n**Date:** ${latest.date}\n\n${latest.update}`);
  };

  return (
    <div className="workspace-grid">
      {/* Left Input/Output Panel */}
      <div className="form-panel">
        <h3>Product One-Pager Synthesizer</h3>
        <p className="subtitle">Configure synthesis target layout.</p>
        <hr />

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Google Cloud product</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g. Compute Engine, Vertex AI"
            />
          </div>

          <button type="submit" className="btn btn-primary full-width">Generate one-pager</button>
        </form>

        {output && (
          <div className="synthesis-output">
            <pre>{output}</pre>
          </div>
        )}
      </div>

      {/* Right Scrollable Panel Ledger */}
      <div className="ledger-panel">
        <h4>Release Notes Ledger</h4>
        <div className="scrolling-ledger">
          {ledgerItems.length === 0 && (
            <p className="note">No release notes match "{productName}".</p>
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
        </div>
      </div>
    </div>
  );
}
