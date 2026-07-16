import React, { useState } from 'react';

const LEDGER = [
  { tag: 'Cloud SQL', note: 'Point-in-time recovery for PostgreSQL 16' },
  { tag: 'Vertex AI', note: 'Gemini Code Assist now in Model Garden' },
  { tag: 'Vertex AI', note: 'Batch prediction quota increased 3x' },
  { tag: 'Compute Engine', note: 'C4 machine series GA in 6 more regions' },
  { tag: 'Cloud SQL', note: 'Per-replica maintenance windows' },
  { tag: 'Compute Engine', note: 'Live migration supports local SSD-attached VMs' }
];

export default function Synthesizer({ defaultProduct }) {
  const [productName, setProductName] = useState(defaultProduct || '');
  const [persona, setPersona] = useState('Cloud Architect');
  const [priority, setPriority] = useState('Critical');
  const [output, setOutput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!productName.trim()) return;
    
    // Simulating backend generated one-pager output
    setOutput(`### MOCK SYNTHESIS ONE-PAGER\n**Product:** ${productName}\n**Audience Focus:** ${persona}\n**Priority Matrix:** ${priority}\n\n[MOCK DATA]: Features successfully evaluated. Under the hood, this release introduces automated pipeline optimizations, scaling logic controls, and structural node adjustments.`);
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
          
          <div className="form-row">
            <div className="input-group">
              <label>Audience persona</label>
              <select value={persona} onChange={(e) => setPersona(e.target.value)}>
                <option>Cloud Architect</option>
                <option>Cloud Sales Representative</option>
                <option>TAM</option>
                <option>Developer</option>
              </select>
            </div>
            <div className="input-group">
              <label>Priority</label>
              <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                <option>Critical</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
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
          {LEDGER.map((item, idx) => {
            const isMatch = productName && item.tag.toLowerCase().includes(productName.toLowerCase());
            return (
              <div key={idx} className="ledger-item">
                <p>{isMatch ? '🔥' : '🔹'} <strong>{item.tag}</strong></p>
                <p className="note">{item.note}</p>
                {idx < LEDGER.length - 1 && <hr />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}