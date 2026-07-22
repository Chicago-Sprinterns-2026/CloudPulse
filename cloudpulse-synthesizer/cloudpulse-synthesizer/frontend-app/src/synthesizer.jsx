import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { useReleaseNotes, useManifest } from './useReleaseNotes';
import { productsMatch } from './utils';
import { GCP_PRODUCTS } from './products';

const RECENT_COUNT = 6;

function matchesProduct(release, query) {
  return release.product.toLowerCase().includes(query.trim().toLowerCase());
}

export default function Synthesizer({ defaultProduct, onViewHistory }) {
  const [productName, setProductName] = useState(defaultProduct || '');
  const [output, setOutput] = useState('');
  const [pdfUrl, setPdfUrl] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

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

  // Catalog entry for the typed/selected product, used for the description
  // blurb above the ledger. Exact match first (this is what a directory
  // click sends in), falls back to fuzzy match for free-typed queries.
  const catalogEntry = useMemo(() => {
    if (!productName.trim()) return null;
    return (
      GCP_PRODUCTS.find((p) => p.name === productName.trim()) ||
      GCP_PRODUCTS.find((p) => productsMatch(p.name, productName)) ||
      null
    );
  }, [productName]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!productName.trim()) return;

    setIsGenerating(true);
    setPdfUrl('');

    try {
      const { data } = await axios.post('http://localhost:8000/api/generate-pdf', {
        product_name: productName.trim(),
      });
      setOutput(data.content_text);
      setPdfUrl(data.pdf_url);
    } catch (error) {
      setOutput('⚠️ Unable to reach the PDF generation backend. Ensure the API server is running on localhost:8000.');
    } finally {
      setIsGenerating(false);
    }
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

          <button type="submit" className="btn btn-primary full-width" disabled={isGenerating}>
            {isGenerating ? 'Generating…' : 'Generate one-pager'}
          </button>
        </form>

        {output && (
          <>
            <div className="synthesis-output" id="one-pager-print">
              <pre>{output}</pre>
            </div>
            <button
              type="button"
              className="btn btn-secondary full-width"
              style={{ marginTop: '10px' }}
              onClick={() => window.print()}
            >
              Export as PDF
            </button>
          </>
        )}
      </div>

      {/* Right Scrollable Panel Ledger */}
      <div className="ledger-panel">
        {catalogEntry && (
          <div className="ledger-service-blurb">
            <span className="ledger-service-name">{catalogEntry.name}</span>
            <span className="ledger-service-category">{catalogEntry.category}</span>
            <p>{catalogEntry.description}</p>
          </div>
        )}

        <h4>Release Notes Ledger</h4>
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
