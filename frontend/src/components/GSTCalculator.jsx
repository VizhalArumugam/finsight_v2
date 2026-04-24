import { useState } from 'react';

export default function GSTCalculator() {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const calculateGST = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/gst/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Request failed');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>GST Tax Advisor</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Describe your business in plain English, and our AI will determine your correct HSN codes, compute your GST liability, and identify if you should register.
      </p>

      <div className="form-group">
        <label>Business Description</label>
        <textarea 
          rows="4" 
          placeholder="e.g., I run a hardware store in Chennai, sell tools and cement, monthly income around 3 lakhs."
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>

      <button className="btn" onClick={calculateGST} disabled={loading || !description.trim()}>
        {loading ? 'Analyzing Business...' : 'Analyze My GST'}
      </button>

      {error && <div className="result-card danger" style={{ marginTop: '1.5rem' }}>{error}</div>}

      {result && (
        <div className="results">
          <h3>Assessment Results</h3>
          <div className="grid">
            <div className="sub-card">
              <h4>Business Understanding</h4>
              <p>Type: <strong>{result.understood.business_type}</strong></p>
              <p>Turnover: <strong>₹{result.understood.turnover_monthly || 0} / mo</strong></p>
              <p>Mode: <strong>{result.understood.sale_mode}</strong></p>
            </div>
            <div className="sub-card">
              <h4>Registration & Filing</h4>
              <p>Status: <span className={`badge ${result.registration.required ? 'danger' : 'success'}`}>{result.registration.status}</span></p>
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>{result.registration.reason}</p>
            </div>
          </div>

          <h4>Applicable HSN Codes</h4>
          {result.gst_items?.map((item, i) => (
            <div key={i} className="result-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <strong>{item.name} (HSN: {item.hsn_sac})</strong>
                <span className="badge warning">{item.gst_rate}% GST</span>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{item.why}</p>
            </div>
          ))}

          {result.advice?.length > 0 && (
            <div className="sub-card" style={{ marginTop: '1.5rem' }}>
              <h4>AI Recommendations</h4>
              <ul style={{ marginTop: '0.5rem' }}>
                {result.advice.map((tip, i) => <li key={i}>{tip}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
