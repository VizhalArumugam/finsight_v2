import { useState } from 'react';

export default function LeakageDetector({ businessType, token }) {
  const getProductsForType = (type) => {
    const map = {
      'Dairy': ['Toned Milk 500ml', 'Full Cream Milk 500ml', 'Curd 400g', 'Paneer 200g'],
      'Grocery': ['Atta 5kg', 'Rice 5kg', 'Sunflower Oil 1L', 'Sugar 1kg'],
      'Hardware': ['Fevicol 200g', 'Asian Paints 1L', 'PVC Pipe 1m', 'Hammer 500g'],
      'Pharmacy': ['Paracetamol strip', 'Sanitizer 100ml']
    };
    return map[type] || ['Generic Product'];
  };
  const catalog = getProductsForType(businessType);

  const [sales, setSales] = useState([{ item: '', qty: 1, price: 0 }]);
  const [deposits, setDeposits] = useState([{ source: '', amount: 0 }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const addSale = () => setSales([...sales, { item: '', qty: 1, price: 0 }]);
  const updateSale = (i, field, value) => {
    const newSales = [...sales];
    newSales[i][field] = value;
    setSales(newSales);
  };
  const removeSale = (i) => setSales(sales.filter((_, idx) => idx !== i));

  const addDeposit = () => setDeposits([...deposits, { source: '', amount: 0 }]);
  const updateDeposit = (i, field, value) => {
    const newDeps = [...deposits];
    newDeps[i][field] = value;
    setDeposits(newDeps);
  };
  const removeDeposit = (i) => setDeposits(deposits.filter((_, idx) => idx !== i));

  const handleRunAudit = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/audit/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ sales, deposits })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to run audit');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Daily Audit & Leakage Detector</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Compare your daily physical sales to your actual payments/cash drawer drops to identify anomalies instantly.
      </p>

      <div className="grid">
        <div className="sub-card">
          <h3>Record Sales</h3>
          {sales.map((s, i) => (
            <div key={i} className="dynamic-row">
              <select value={s.item} onChange={e => updateSale(i, 'item', e.target.value)} style={{ flex: '1' }}>
                <option value="">-- Product --</option>
                {catalog.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <input 
                type="number" 
                placeholder="Qty" style={{ flex: '0.3' }}
                value={s.qty} 
                onChange={e => updateSale(i, 'qty', e.target.value)} 
              />
              <input 
                type="number" 
                placeholder="Price" style={{ flex: '0.4' }}
                value={s.price} 
                onChange={e => updateSale(i, 'price', e.target.value)} 
              />
              <button className="btn btn-small btn-danger" onClick={() => removeSale(i)}>✕</button>
            </div>
          ))}
          <button className="btn btn-small" onClick={addSale}>+ Add Sale Item</button>
        </div>

        <div className="sub-card">
          <h3>Record Deposits</h3>
          {deposits.map((d, i) => (
            <div key={i} className="dynamic-row">
              <input 
                type="text" 
                placeholder="Payment Source (e.g. Cash, UPI)"
                value={d.source} 
                onChange={e => updateDeposit(i, 'source', e.target.value)} 
              />
              <input 
                type="number" 
                placeholder="Amount" style={{ flex: '0.4' }}
                value={d.amount} 
                onChange={e => updateDeposit(i, 'amount', e.target.value)} 
              />
              <button className="btn btn-small btn-danger" onClick={() => removeDeposit(i)}>✕</button>
            </div>
          ))}
          <button className="btn btn-small" onClick={addDeposit}>+ Add Deposit Drop</button>
        </div>
      </div>

      <button className="btn" onClick={handleRunAudit} disabled={loading}>
        {loading ? 'Running AI Audit...' : 'Run Leakage Audit'}
      </button>

      {error && <div className="result-card danger" style={{ marginTop: '1.5rem' }}>{error}</div>}

      {result && (
        <div className="results">
          <h3>Audit Results</h3>
          <div className={`result-card ${result.status === 'clean' ? 'success' : result.status === 'critical' ? 'danger' : 'warning'}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>Status: <span className={`badge ${result.status === 'clean' ? 'success' : result.status === 'critical' ? 'danger' : 'warning'}`}>{result.status}</span></span>
              <span style={{ fontSize: '1.25rem' }}>Mismatch: <strong>₹{result.mismatch}</strong> ({result.mismatch_pct}%)</span>
            </div>
            
            <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '1rem' }}>{result.ai_report}</p>
            
            {result.anomalies?.length > 0 && (
              <>
                <h4 style={{ marginBottom: '0.5rem' }}>Potential Anomalies</h4>
                <ul>
                  {result.anomalies.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </>
            )}
            
            {result.action_steps?.length > 0 && (
              <>
                <h4 style={{ marginBottom: '0.5rem' }}>Recommended Actions</h4>
                <ul>
                  {result.action_steps.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
