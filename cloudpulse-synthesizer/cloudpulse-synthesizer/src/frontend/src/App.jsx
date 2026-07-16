import React, { useState, useEffect } from 'react';

import "./css/app.css";      
import Catalog from "./catalog";    
import Synthesizer from "./synthesizer"; 
import Chatbot from "./chatbot";

export default function App() {
  // --- Core Application View Routing State ---
  const [viewState, setViewState] = useState('carousel');
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [selectedProduct, setSelectedProduct] = useState('Compute Engine');

  // --- Automatic Rotating Carousel Timer Logic ---
  useEffect(() => {
    if (viewState !== 'carousel') return;
    const interval = setInterval(() => {
      setCarouselIndex((prev) => (prev + 1) % 4);
    }, 5000);
    return () => clearInterval(interval);
  }, [viewState]);

  return (
    <div className="app-container">
      {/* GLOBAL TOP NAVBAR HEADER */}
      <header className="global-header-bar">
        <div className="brand" onClick={() => setViewState('carousel')} style={{ cursor: 'pointer' }}>
          <span style={{ fontSize: '1.4rem', marginRight: '8px' }}>☁️</span>
          <strong style={{ fontSize: '1.1rem', color: '#202124' }}>CloudPulse Engine Workspace</strong>
        </div>

        <div className="header-right-actions">
          {viewState === 'catalog' && (
            <button className="btn btn-primary" onClick={() => setViewState('login')}>Sign In</button>
          )}
          {viewState === 'synthesizer' && (
            <select 
              value={selectedProduct} 
              onChange={(e) => setSelectedProduct(e.target.value)} 
              style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #B0B3B8' }}
            >
              <option>Compute Engine</option>
              <option>Vertex AI</option>
              <option>Cloud SQL</option>
            </select>
          )}
        </div>
      </header>

      {/* CORE CONTENT SWITCH ROUTER */}
      <main className="main-content">
        {/* VIEW 1: STAGE CAROUSEL */}
        {viewState === 'carousel' && (
          <div className="carousel-view">
            <div className="carousel-frame">
              <button className="arrow-btn" onClick={() => setCarouselIndex((prev) => (prev - 1 + 4) % 4)}>❬</button>
              <div className="carousel-card">
                <h2>Google Cloud Feature Track {carouselIndex + 1}</h2>
                <p>Automatic synthesis overview panel highlighting active branch changelogs.</p>
              </div>
              <button className="arrow-btn" onClick={() => setCarouselIndex((prev) => (prev + 1) % 4)}>❭</button>
            </div>
            
            <div className="dots-container">
              {[0, 1, 2, 3].map((i) => (
                <span key={i} className={`dot ${i === carouselIndex ? 'active' : ''}`} />
              ))}
            </div>

            <div className="carousel-actions">
              <button className="btn btn-secondary" onClick={() => setViewState('catalog')}>See More</button>
              <button className="btn btn-primary-dark" onClick={() => setViewState('login')}>Sign In</button>
            </div>
          </div>
        )}

        {/* VIEW 2: PRODUCT CATALOG */}
        {viewState === 'catalog' && (
          <Catalog onSelectProduct={(productName) => {
            setSelectedProduct(productName);
            setViewState('login');
          }} />
        )}

        {/* VIEW 3: ACCOUNT LOGIN */}
        {viewState === 'login' && (
          <div className="login-view">
            <div className="login-card">
              <h3>🔐 Account Authentication</h3>
              <div className="input-group">
                <label>Corporate ID Email</label>
                <input type="email" placeholder="name@company.com" />
              </div>
              <div className="input-group">
                <label>Security Key / Access Phrase</label>
                <input type="password" />
              </div>
              <button className="btn btn-primary full-width" onClick={() => setViewState('synthesizer')}>
                Authenticate Workspace Access
              </button>
            </div>
          </div>
        )}

        {/* VIEW 4: INTERACTIVE WORKSPACE */}
        {viewState === 'synthesizer' && (
          <div className="workspace-view">
            <Synthesizer defaultProduct={selectedProduct} />
          </div>
        )}
      </main>

      {/* GLOBAL POSITIONED FOOTER HUD BAR */}
      <footer className="global-footer-bar">
        <div style={{ fontSize: '0.85rem', color: '#5F6368' }}>
          Status: <span style={{ color: '#0F9D58', fontWeight: 'bold' }}>● Operational</span> (Mock Mode Engine)
        </div>
        
        {/* Persistent bottom-horizon troubleshooting tray layout toggled by view index */}
        {viewState === 'synthesizer' ? (
          <div style={{ width: '450px' }}>
            <Chatbot />
          </div>
        ) : (
          <div style={{ fontSize: '0.85rem', color: '#9AA0A6' }}>
            Secure session environment backed by enterprise workspace credentials.
          </div>
        )}
      </footer>
    </div>
  );
}