import { useState, useEffect } from 'react';
import './index.css';
import GSTCalculator from './components/GSTCalculator';
import PriceValidator from './components/PriceValidator';
import LeakageDetector from './components/LeakageDetector';
import InventoryROP from './components/InventoryROP';
import ABCClassifier from './components/ABCClassifier';

/* ── Theme helpers ── */
function getInitialTheme() {
  const saved = localStorage.getItem('finsight-theme');
  if (saved === 'dark' || saved === 'light') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('finsight-theme', theme);
}

/* ── Sun / Moon SVG icons ── */
const SunIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1"  x2="12" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22"  x2="5.64" y2="5.64"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1"  y1="12" x2="3"  y2="12"/>
    <line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64"  y2="18.36"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);
const MoonIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

const TABS = [
  { id: 'price',     label: 'Price Validator'   },
  { id: 'audit',     label: 'Leakage Detector'  },
  { id: 'gst',       label: 'GST Advisor'       },
  { id: 'inventory', label: 'Inventory ROP'     },
  { id: 'abc',       label: 'ABC Classifier'    },
];

function App() {
  const [theme, setTheme] = useState(getInitialTheme);
  const [profile, setProfile]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState('price');

  // Login form state
  const [ownerName,    setOwnerName]    = useState('');
  const [shopName,     setShopName]     = useState('');
  const [businessType, setBusinessType] = useState('Grocery');

  /* Apply theme on mount + change */
  useEffect(() => { applyTheme(theme); }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  /* Load profile */
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/profile/get`)
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setProfile(data.data); })
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        owner_name: ownerName,
        shop_name: shopName || 'My Store',
        business_type: businessType,
      };
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/profile/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) setProfile(payload);
    } catch (err) {
      console.error(err);
    }
  };

  /* ── Loading ── */
  if (loading) return (
    <div className="container" style={{ textAlign: 'center', marginTop: '6rem', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '1.1rem', fontWeight: 500 }}>Loading FinSight…</div>
    </div>
  );

  /* ── Profile setup ── */
  if (!profile) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
        {/* Theme toggle — even on login */}
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          style={{ position: 'fixed', top: '1.25rem', right: '1.25rem' }}
        >
          {theme === 'light' ? <MoonIcon /> : <SunIcon />}
        </button>

        <div style={{ width: '100%', maxWidth: '460px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)', letterSpacing: '-0.03em', marginBottom: '0.4rem' }}>
              FinSight
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              AI-powered business intelligence for Indian retailers
            </p>
          </div>

          <div className="card">
            <h2 style={{ marginBottom: '0.35rem' }}>Set up your profile</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.75rem' }}>
              Tell us about your business to get personalised insights.
            </p>

            <form onSubmit={handleSaveProfile}>
              <div className="form-group">
                <label>Owner Name</label>
                <input
                  type="text"
                  required
                  value={ownerName}
                  onChange={e => setOwnerName(e.target.value)}
                  placeholder="e.g. Rahul Kumar"
                />
              </div>
              <div className="form-group">
                <label>Shop Name</label>
                <input
                  type="text"
                  value={shopName}
                  onChange={e => setShopName(e.target.value)}
                  placeholder="e.g. Rahul Supermart"
                />
              </div>
              <div className="form-group">
                <label>Business Type</label>
                <select value={businessType} onChange={e => setBusinessType(e.target.value)}>
                  <option value="Grocery">Grocery</option>
                  <option value="Dairy">Dairy</option>
                  <option value="Hardware">Hardware</option>
                  <option value="Pharmacy">Pharmacy</option>
                  <option value="Electronics">Electronics</option>
                  <option value="Clothing">Clothing</option>
                  <option value="Restaurant">Restaurant</option>
                  <option value="Services">Services</option>
                </select>
              </div>
              <button type="submit" className="btn">Get Started</button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  /* ── Main workspace ── */
  return (
    <div className="container">

      {/* Header */}
      <div className="app-header">
        <div className="app-header-left">
          <div className="app-title">
            Fin<span>Sight</span>
          </div>
          <div className="app-subtitle">
            Welcome back, <strong>{profile.owner_name}</strong> · {profile.business_type}
          </div>
        </div>
        <div className="app-header-right">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <MoonIcon /> : <SunIcon />}
          </button>
          <button className="btn-small btn-danger" onClick={() => setProfile(null)}>
            Change Profile
          </button>
        </div>
      </div>

      {/* Tabs */}
      <nav className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main>
        {activeTab === 'price'     && <PriceValidator businessType={profile.business_type} />}
        {activeTab === 'audit'     && <LeakageDetector businessType={profile.business_type} />}
        {activeTab === 'gst'       && <GSTCalculator />}
        {activeTab === 'inventory' && <InventoryROP businessType={profile.business_type} />}
        {activeTab === 'abc'       && <ABCClassifier businessType={profile.business_type} />}
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '2.5rem 0 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        FinSight v2.0 — AI Business Intelligence
      </footer>
    </div>
  );
}

export default App;
