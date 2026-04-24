import { useState } from 'react';

export default function PriceValidator({ businessType, token }) {
  const getProductsForType = (type) => {
    const map = {
      'Dairy': ['Toned Milk 500ml', 'Full Cream Milk 500ml', 'Curd 400g', 'Ghee 500ml', 'Butter 100g', 'Paneer 200g'],
      'Grocery': ['Atta 5kg', 'Rice 5kg', 'Sunflower Oil 1L', 'Sugar 1kg', 'Toor Dal 1kg', 'Tea 500g', 'Tomato 1kg', 'Onion 1kg', 'Potato 1kg'],
      'Hardware': ['Fevicol 200g', 'Asian Paints 1L', 'PVC Pipe 1m', 'Electrical Wire 10m', 'Hammer 500g'],
      'Pharmacy': ['Paracetamol strip', 'Sanitizer 100ml'],
      'Electronics': ['LED Bulb 9W', 'USB Cable 1m']
    };
    return map[type] || ['Generic Product 1'];
  };

  const products = getProductsForType(businessType);

  const [product, setProduct] = useState('');
  const [price, setPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const validatePrice = async () => {
    if (!product || !price) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/price/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ product, category: businessType || 'General', your_price: Number(price) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Request failed');
      setResult(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Market Price Validator</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Check if your product pricing is competitive against real-time web limits (or AI estimates) in the Indian market.
      </p>

      <div className="grid" style={{ marginBottom: '1.5rem' }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label>Product Name</label>
          <select value={product} onChange={e => setProduct(e.target.value)}>
            <option value="">-- Select Product --</option>
            {products.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label>Category</label>
          <input 
            type="text" 
            value={businessType || ''}
            disabled
            readOnly
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label>Your Price (₹)</label>
          <input 
            type="number" 
            placeholder="e.g. 32"
            value={price}
            onChange={e => setPrice(e.target.value)}
          />
        </div>
      </div>

      <button className="btn" onClick={validatePrice} disabled={loading || !product || !price}>
        {loading ? 'Validating Market Data...' : 'Validate Price'}
      </button>

      {error && <div className="result-card danger" style={{ marginTop: '1.5rem' }}>{error}</div>}

      {result && (
        <div className="results">
          <div className={`result-card ${result.verdict === 'fair' ? 'success' : result.verdict === 'overpriced' ? 'danger' : 'warning'}`}>
            <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>Verdict: <span className={`badge ${result.verdict === 'fair' ? 'success' : result.verdict === 'overpriced' ? 'danger' : 'warning'}`}>{result.verdict}</span></span>
            
            <div className="grid" style={{ marginTop: '1.5rem' }}>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Market Source</p>
                <strong>{result.market.source}</strong>
              </div>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Market Average</p>
                <strong>₹{result.market.avg} {result.market.unit}</strong>
              </div>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Difference</p>
                <strong style={{ color: result.diff_percent > 0 ? 'var(--danger)' : 'var(--success)' }}>
                  {result.diff_percent}% (₹{Math.abs(result.diff_absolute)})
                </strong>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '1.5rem 0' }} />
            
            <div style={{ background: 'var(--bg-muted)', padding: '1rem 1.25rem', borderRadius: '0.75rem', marginBottom: '1rem', border: '1px solid var(--border)' }}>
              <p style={{ marginBottom: '0.5rem' }}><strong>Analysis:</strong> {result.price_position}</p>
              <p style={{ marginBottom: '0.5rem', color: 'var(--danger)' }}><strong>Cheaper At:</strong> {result.selling_less_where}</p>
              <p><strong>Strategic Suggestion:</strong> {result.suggestion}</p>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Market Context: {result.competitive_context}</p>

            {result.live_links && result.live_links.length > 0 && (
              <div style={{ marginTop: '1.5rem', background: 'var(--bg-muted)', padding: '1.25rem', borderRadius: '0.875rem', border: '1px solid var(--border)' }}>
                <p style={{ marginBottom: '1rem', fontWeight: 700, color: 'var(--text-main)', fontSize: '0.95rem', letterSpacing: '0.01em' }}>
                  🛒 Verify Live Prices Directly:
                </p>
                <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                  {result.live_links.map((link, idx) => (
                    <a
                      key={idx}
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="store-link-btn"
                    >
                      {link.store}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
