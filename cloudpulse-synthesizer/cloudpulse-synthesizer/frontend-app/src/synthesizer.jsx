import React from 'react';
import { useManifest } from './useReleaseNotes';
import Chatbot from './chatbot';

// The Workspace page is now just the chatbot, full-page. Release notes are
// no longer surfaced here — they stay reachable the way they already are,
// via each product's own page (Documentation / Release History tabs).
export default function Synthesizer({ defaultProduct }) {
  const { manifest } = useManifest();

  return (
    <div className="workspace-view-full">
      <div className="workspace-title-row">
        <h3 className="workspace-title">💬 CloudPulse Assistant</h3>
        <span className="workspace-subtitle">
          Ask a question, or generate a one-pager for any Google Cloud product.
        </span>
      </div>
      <div className="chat-panel chat-panel-full">
        <Chatbot product={defaultProduct} manifest={manifest} />
      </div>
      <p className="workspace-disclaimer">AI can be wrong. Please double check all responses.</p>
    </div>
  );
}
