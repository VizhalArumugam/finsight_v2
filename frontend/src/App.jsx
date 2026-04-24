import { useState, useEffect, useCallback } from 'react';
import './index.css';
import GSTCalculator from './components/GSTCalculator';
import PriceValidator from './components/PriceValidator';
import LeakageDetector from './components/LeakageDetector';
import InventoryROP from './components/InventoryROP';
import ABCClassifier from './components/ABCClassifier';
import ProfileSettings from './components/ProfileSettings';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000';

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
  { id: 'price',     label: 'Price Validator'  },
  { id: 'audit',     label: 'Leakage Detector' },
  { id: 'gst',       label: 'GST Advisor'      },
  { id: 'inventory', label: 'Inventory ROP'    },
  { id: 'abc',       label: 'ABC Classifier'   },
  { id: 'settings',  label: 'Profile'      },
];

export default function App() {
  const [theme, setTheme]       = useState(getInitialTheme);
  const [user, setUser]         = useState(null);
  const [token, setToken]       = useState(() => localStorage.getItem('finsight-token'));
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState('price');

  /* Auth form state */
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail]             = useState('');
  const [password, setPassword]       = useState('');
  const [ownerName, setOwnerName]     = useState('');
  const [shopName, setShopName]       = useState('');
  const [businessType, setBusinessType] = useState('Grocery');
  const [authError, setAuthError]     = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  /* Apply theme */
  useEffect(() => { applyTheme(theme); }, [theme]);
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  /* Verify existing token on mount */
  useEffect(() => {
    if (!token) { setLoading(false); return; }
    fetch(`${API}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success') setUser(data.user);
        else { localStorage.removeItem('finsight-token'); setToken(null); }
      })
      .catch(() => { localStorage.removeItem('finsight-token'); setToken(null); })
      .finally(() => setLoading(false));
  }, [token]);

  /* Store token helper */
  const handleAuthSuccess = useCallback((tok, userData) => {
    localStorage.setItem('finsight-token', tok);
    setToken(tok);
    setUser(userData);
    setAuthError('');
  }, []);

  /* Login submit */
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError(''); setAuthLoading(true);
    try {
      const res  = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');
      handleAuthSuccess(data.token, data.user);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  /* Register submit */
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError(''); setAuthLoading(true);
    try {
      const res  = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, owner_name: ownerName, shop_name: shopName, business_type: businessType }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Registration failed');
      handleAuthSuccess(data.token, data.user);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  /* Logout */
  const handleLogout = () => {
    localStorage.removeItem('finsight-token');
    setToken(null);
    setUser(null);
    setEmail(''); setPassword(''); setOwnerName('');
  };

  /* ── Loading ── */
  if (loading) return (
    <div className="container" style={{ textAlign: 'center', marginTop: '6rem', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '1.1rem', fontWeight: 500 }}>Loading FinSight…</div>
    </div>
  );

  /* ── Auth Screen ── */
  if (!user) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
        <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} style={{ position: 'fixed', top: '1.25rem', right: '1.25rem' }}>
          {theme === 'light' ? <MoonIcon /> : <SunIcon />}
        </button>

        <div style={{ width: '100%', maxWidth: '460px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)', letterSpacing: '-0.03em', marginBottom: '0.4rem' }}>FinSight</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>AI-powered business intelligence for Indian retailers</p>
          </div>

          <div className="card">
            {/* Tab toggle */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.75rem', background: 'var(--bg-alt)', borderRadius: '8px', padding: '4px' }}>
              {['login', 'register'].map(mode => (
                <button key={mode} onClick={() => { setAuthMode(mode); setAuthError(''); }}
                  style={{ flex: 1, padding: '0.5rem', borderRadius: '6px', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem',
                    background: authMode === mode ? 'var(--primary)' : 'transparent',
                    color: authMode === mode ? '#fff' : 'var(--text-muted)',
                    transition: 'all 0.2s' }}>
                  {mode === 'login' ? 'Login' : 'Create Account'}
                </button>
              ))}
            </div>

            {authMode === 'login' ? (
              <form onSubmit={handleLogin}>
                <div className="form-group">
                  <label>Email</label>
                  <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input type="password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
                </div>
                {authError && <div className="result-card danger" style={{ marginBottom: '1rem', padding: '0.75rem 1rem' }}>{authError}</div>}
                <button type="submit" className="btn" disabled={authLoading}>{authLoading ? 'Logging in…' : 'Login'}</button>
              </form>
            ) : (
              <form onSubmit={handleRegister}>
                <div className="form-group">
                  <label>Email</label>
                  <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
                </div>
                <div className="form-group">
                  <label>Password (min 6 characters)</label>
                  <input type="password" required minLength={6} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
                </div>
                <div className="form-group">
                  <label>Owner Name</label>
                  <input type="text" required value={ownerName} onChange={e => setOwnerName(e.target.value)} placeholder="e.g. Rahul Kumar" />
                </div>
                <div className="form-group">
                  <label>Shop Name</label>
                  <input type="text" value={shopName} onChange={e => setShopName(e.target.value)} placeholder="e.g. Rahul Supermart" />
                </div>
                <div className="form-group">
                  <label>Business Type</label>
                  <select value={businessType} onChange={e => setBusinessType(e.target.value)}>
                    {['Grocery','Dairy','Hardware','Pharmacy','Electronics','Clothing','Restaurant','Services'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                {authError && <div className="result-card danger" style={{ marginBottom: '1rem', padding: '0.75rem 1rem' }}>{authError}</div>}
                <button type="submit" className="btn" disabled={authLoading}>{authLoading ? 'Creating account…' : 'Get Started'}</button>
              </form>
            )}
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
          <div className="app-title">Fin<span>Sight</span></div>
          <div className="app-subtitle">Welcome back, <strong>{user.owner_name}</strong> · {user.business_type}</div>
        </div>
        <div className="app-header-right">
          <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
            {theme === 'light' ? <MoonIcon /> : <SunIcon />}
          </button>
          <button className="btn-small btn-danger" onClick={handleLogout}>Log Out</button>
        </div>
      </div>

      {/* Tabs */}
      <nav className="tabs">
        {TABS.map(tab => (
          <button key={tab.id} className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content — pass token to all components */}
      <main>
        {activeTab === 'price'     && <PriceValidator     businessType={user.business_type} token={token} />}
        {activeTab === 'audit'     && <LeakageDetector    businessType={user.business_type} token={token} />}
        {activeTab === 'gst'       && <GSTCalculator      token={token} />}
        {activeTab === 'inventory' && <InventoryROP       businessType={user.business_type} token={token} />}
        {activeTab === 'abc'       && <ABCClassifier      businessType={user.business_type} token={token} />}
        {activeTab === 'settings'  && <ProfileSettings    user={user} token={token} onUpdateUser={setUser} />}
      </main>

      <footer style={{ textAlign: 'center', padding: '2.5rem 0 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        FinSight v2.0 — AI Business Intelligence
      </footer>
    </div>
  );
}
