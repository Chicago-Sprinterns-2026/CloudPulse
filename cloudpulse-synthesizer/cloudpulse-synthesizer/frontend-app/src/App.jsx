import React, { useState, useEffect } from 'react';

import "./css/App.css";
import Catalog from "./catalog";    
import Synthesizer from "./synthesizer"; 
import Chatbot from "./chatbot";
import ProductDirectory from "./productDirectory";
import Dashboard from "./dashboard";
import ReleaseHistory from "./releaseHistory";
import { GCP_PRODUCTS, CATEGORIES } from "./products";
import googleCloudIcon from "./assets/google-cloud-icon.png";

//Real brand colors.
const BRAND_COLORS = ['var(--g-blue)', 'var(--g-red)', 'var(--g-yellow)', 'var(--g-green)'];

// Carousel slides: one per category, each spotlighting up to 4 example
// products from that category.
function buildCarouselSlides() {
  return CATEGORIES.map((category) => ({
    category,
    products: GCP_PRODUCTS.filter((p) => p.category === category).slice(0, 4),
  })).filter((slide) => slide.products.length > 0);
}

const CAROUSEL_SLIDES = buildCarouselSlides();

// Back-button label on the release history page, based on which view sent
// the user there.
const HISTORY_ORIGIN_LABELS = {
  synthesizer: '← Back to workspace',
  catalog: '← Back to recent updates',
  products: '← Back to all products',
};

// One-line blurb per category for the carousel caption. 
const CATEGORY_BLURBS = {
  'Compute': 'Run workloads on VMs, containers, or fully managed serverless.',
  'Storage': 'Object, block, and file storage for any workload.',
  'Databases': 'Managed relational, NoSQL, and in-memory databases.',
  'Data Analytics': 'Ingest, process, and analyze data at any scale.',
  'AI & Machine Learning': 'Build, train, and deploy models — or use them pretrained.',
  'Networking': 'Connect and secure workloads across the globe.',
  'Security & Identity': 'Protect users, data, and workloads by default.',
  'DevOps & Management': 'Ship, monitor, and operate software reliably.',
  'Hybrid & Multicloud': 'Run consistently across on-prem and other clouds.',
  'Migration': 'Move workloads and data into Google Cloud.',
  'Application Integration': 'Connect services, events, and workflows.',
  'Media & Gaming': 'Encode, stream, and serve media and game infrastructure.',
};

export default function App() {
  const [viewState, setViewState] = useState('carousel');
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [slideDirection, setSlideDirection] = useState('next');
  const [selectedProduct, setSelectedProduct] = useState('Compute Engine');
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [historyProduct, setHistoryProduct] = useState(null);
  const [historyOrigin, setHistoryOrigin] = useState('synthesizer');

  // Carousel timing logic
  useEffect(() => {
    if (viewState !== 'carousel') return;
    const interval = setInterval(() => {
      setSlideDirection('next');
      setCarouselIndex((prev) => (prev + 1) % CAROUSEL_SLIDES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [viewState]);

  const goToCarouselSlide = (index, direction) => {
    setSlideDirection(direction);
    setCarouselIndex(index);
  };

  const activeSlide = CAROUSEL_SLIDES[carouselIndex];

  return (
    <div className="app-container">
      <header className="global-header-bar">
        <div className="brand" onClick={() => setViewState(isSignedIn ? 'dashboard' : 'carousel')} style={{ cursor: 'pointer' }}>
          <img src={googleCloudIcon} alt="Google Cloud" style={{ width: '22px', height: '20px', marginRight: '8px' }} />
          <strong style={{ fontSize: '1.1rem', color: '#202124' }}>CloudPulse</strong>
        </div>

        <div className="header-right-actions">
          {!isSignedIn && (viewState === 'catalog' || viewState === 'products') && (
            <button className="btn btn-primary" onClick={() => setViewState('login')}>Sign In</button>
          )}

          {isSignedIn && (
            <nav className="header-nav">
              <button
                className={`header-nav-link ${viewState === 'dashboard' ? 'active' : ''}`}
                onClick={() => setViewState('dashboard')}
              >
                Dashboard
              </button>
              <button
                className={`header-nav-link ${viewState === 'products' ? 'active' : ''}`}
                onClick={() => setViewState('products')}
              >
                Products
              </button>
              <button
                className={`header-nav-link ${(viewState === 'synthesizer' || viewState === 'history') ? 'active' : ''}`}
                onClick={() => setViewState('synthesizer')}
              >
                Workspace
              </button>
            </nav>
          )}

          {isSignedIn && (
            <div className="account-menu-wrapper">
              <button
                className="account-button"
                onClick={() => setAccountMenuOpen((open) => !open)}
              >
                👤 Account
              </button>

              {accountMenuOpen && (
                <div className="account-dropdown">
                  <button
                    onClick={() => {
                      setAccountMenuOpen(false);
                      setIsSignedIn(false);
                      setViewState('carousel');
                    }}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        {/* carousel view*/}
        {viewState === 'carousel' && (
          <div className="carousel-view">
            <div className="carousel-frame">
              <button
                className="arrow-btn"
                aria-label="Previous category"
                onClick={() => goToCarouselSlide((carouselIndex - 1 + CAROUSEL_SLIDES.length) % CAROUSEL_SLIDES.length, 'prev')}
              >
                ❬
              </button>

              <div className="carousel-band">
                <div className="carousel-tiles-viewport">
                  <div className={`carousel-tiles slide-${slideDirection}`} key={carouselIndex}>
                    {activeSlide.products.map((prod, i) => (
                      <button
                        key={prod.name}
                        className="carousel-tile active"
                        style={{ '--tile-color': BRAND_COLORS[i % 4] }}
                        onClick={() => {
                          setSelectedProduct(prod.name);
                          setViewState('login');
                        }}
                      >
                        <span className="tile-swatch" />
                        <span className="tile-label">{prod.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="dots-container">
                  {CAROUSEL_SLIDES.map((slide, i) => (
                    <span
                      key={slide.category}
                      className={`dot ${i === carouselIndex ? 'active' : ''}`}
                      style={{ '--dot-color': BRAND_COLORS[i % 4] }}
                      onClick={() => goToCarouselSlide(i, i > carouselIndex ? 'next' : 'prev')}
                    />
                  ))}
                </div>
              </div>

              <button
                className="arrow-btn"
                aria-label="Next category"
                onClick={() => goToCarouselSlide((carouselIndex + 1) % CAROUSEL_SLIDES.length, 'next')}
              >
                ❭
              </button>
            </div>

            <div className="carousel-caption-viewport">
              <div className={`carousel-caption slide-${slideDirection}`} key={carouselIndex}>
                <h2>{activeSlide.category}</h2>
                <p>{CATEGORY_BLURBS[activeSlide.category] || 'Explore this category of Google Cloud products.'}</p>
              </div>
            </div>

            <div className="carousel-actions">
              <button className="btn btn-pill" onClick={() => setViewState('products')}>See all {GCP_PRODUCTS.length} products</button>
              <button className="btn btn-primary-dark" onClick={() => setViewState('login')}>Sign in</button>
            </div>
          </div>
        )}

        {/* Product Browsing View */}
        {(viewState === 'products' || viewState === 'catalog') && (
          <div className="browse-view">
            <div className="browse-tabs">
              <button
                className={`browse-tab ${viewState === 'products' ? 'active' : ''}`}
                onClick={() => setViewState('products')}
              >
                All products
              </button>
              <button
                className={`browse-tab ${viewState === 'catalog' ? 'active' : ''}`}
                onClick={() => setViewState('catalog')}
              >
                Recent updates
              </button>
            </div>

            {viewState === 'products' && (
              <ProductDirectory
                onSelectProduct={(productName) => {
                  setSelectedProduct(productName);
                  setViewState('login');
                }}
                onViewHistory={(productName) => {
                  setHistoryProduct(productName);
                  setHistoryOrigin('products');
                  setViewState('history');
                }}
              />
            )}

            {viewState === 'catalog' && (
              <Catalog
                onSelectProduct={(productName) => {
                  setSelectedProduct(productName);
                  setViewState('login');
                }}
                onViewHistory={(productName) => {
                  setHistoryProduct(productName);
                  setHistoryOrigin('catalog');
                  setViewState('history');
                }}
              />
            )}
          </div>
        )}

        {/* Login View*/}
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
              <button
                className="btn btn-primary full-width"
                onClick={() => {
                  setIsSignedIn(true);
                  setViewState('dashboard');
                }}
              >
                Authenticate Workspace Access
              </button>
            </div>
          </div>
        )}

        {/* Dashboard post sign in */}
        {viewState === 'dashboard' && isSignedIn && (
          <Dashboard onSelectProduct={(productName) => {
            setSelectedProduct(productName);
            setViewState('synthesizer');
          }} />
        )}

        {/* Synthesizer view */}
        {viewState === 'synthesizer' && (
          <div className="workspace-view">
            <Synthesizer
              defaultProduct={selectedProduct}
              onViewHistory={(product) => {
                setHistoryProduct(product);
                setHistoryOrigin('synthesizer');
                setViewState('history');
              }}
            />
          </div>
        )}

        {/* Release History View */}
        {viewState === 'history' && historyProduct && (
          <ReleaseHistory
            product={historyProduct}
            backLabel={HISTORY_ORIGIN_LABELS[historyOrigin]}
            onBack={() => setViewState(historyOrigin)}
          />
        )}
      </main>

      
      <footer className={`global-footer-bar ${isSignedIn ? 'has-chat-dock' : ''}`}>
        {isSignedIn ? (
          <div className="footer-chat-dock">
            <Chatbot />
          </div>
        ) : (
          <>
            <div style={{ fontSize: '0.85rem', color: '#5F6368' }}>
              Status: <span style={{ color: '#0F9D58', fontWeight: 'bold' }}>● Operational</span> (Mock Mode Engine)
            </div>
            <div style={{ fontSize: '0.85rem', color: '#9AA0A6' }}>
              Secure session environment backed by enterprise workspace credentials.
            </div>
          </>
        )}
      </footer>
    </div>
  );
}