import { useState, useRef } from 'react';
import Papa from 'papaparse';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip as RechartsTooltip, Legend, Cell } from 'recharts';

export default function InventoryROP({ businessType }) {
  const fileInputRef = useRef(null);
  
  const [product, setProduct] = useState('');
  const [avgDailySales, setAvgDailySales] = useState(0);
  const [leadTime, setLeadTime] = useState(0);
  const [safetyStock, setSafetyStock] = useState(0);
  const [currentStock, setCurrentStock] = useState(0);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const getProductsForType = (type) => {
    const map = {
      'Dairy': ['Toned Milk 500ml', 'Full Cream Milk 500ml', 'Curd 400g', 'Paneer 200g'],
      'Grocery': ['Atta 5kg', 'Rice 5kg', 'Sunflower Oil 1L', 'Sugar 1kg', 'Toor Dal 1kg'],
      'Hardware': ['Fevicol 200g', 'Asian Paints 1L', 'PVC Pipe 1m', 'Hammer 500g'],
      'Pharmacy': ['Paracetamol strip', 'Sanitizer 100ml']
    };
    return map[type] || ['Generic Product 1', 'Generic Product 2'];
  };

  const products = getProductsForType(businessType);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (parsedOutput) => {
        const payload = parsedOutput.data.map((row, i) => ({
          product: row.name || row['Product Name'] || row.item || `Item ${i+1}`,
          avg_daily_sales: Number(row.avg_daily_sales || row['Daily Sales'] || row.qty || 0),
          lead_time_days: Number(row.lead_time_days || row['Lead Time'] || 7),
          safety_stock: Number(row.safety_stock || row['Safety Stock'] || row.price || 0),
          current_stock: Number(row.current_stock || row['Current Stock'] || row.stock || 0)
        }));
        
        await calculateROPBulk(payload);
      },
      error: (err) => {
        setError(`Failed to parse CSV: ${err.message}`);
      }
    });
    e.target.value = null;
  };

  const calculateROPSingle = async () => {
    if (!product) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/inventory/rop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          product, 
          avg_daily_sales: avgDailySales, 
          lead_time_days: leadTime, 
          safety_stock: safetyStock, 
          current_stock: currentStock 
        })
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

  const calculateROPBulk = async (bulkProducts) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/inventory/rop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ products: bulkProducts })
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

  const getBulkChartData = () => {
    if (!result || !result.batch) return [];
    // Sort by urgent orders
    const sorted = [...result.results].sort((a, b) => a.days_until_stockout - b.days_until_stockout);
    return sorted.slice(0, 15).map(r => ({
      name: r.product.length > 12 ? r.product.substring(0, 12) + '...' : r.product,
      currentStock: r.current_stock,
      suggestedOrder: r.order_quantity_suggested,
      isDanger: r.status === 'order_now'
    }));
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Inventory Reorder Point (ROP)</h2>
          <div>
            <input 
                type="file" 
                accept=".csv" 
                ref={fileInputRef} 
                style={{ display: 'none' }} 
                onChange={handleFileUpload}
            />
            <button 
                className="btn-small" 
                style={{ backgroundColor: 'var(--text-main)', color: '#fff' }}
                onClick={() => fileInputRef.current.click()}
                disabled={loading}
              >
                Upload CSV Sheet
              </button>
          </div>
      </div>
      
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', marginTop: '0.5rem' }}>
        Calculate exactly when to restock inventory to avoid stockouts while minimizing holding costs. Upload a `.csv` to analyze massive catalogs at once.
      </p>

      <div className="grid" style={{ marginBottom: '1.5rem' }}>
        <div className="form-group">
          <label>Product</label>
          <select value={product} onChange={e => setProduct(e.target.value)}>
            <option value="">-- Select Product --</option>
            {products.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Avg Daily Sales (Units)</label>
          <input type="number" value={avgDailySales} onChange={e => setAvgDailySales(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label>Vendor Lead Time (Days)</label>
          <input type="number" value={leadTime} onChange={e => setLeadTime(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label>Safety Stock Target</label>
          <input type="number" value={safetyStock} onChange={e => setSafetyStock(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label>Current Stock in store</label>
          <input type="number" value={currentStock} onChange={e => setCurrentStock(Number(e.target.value))} />
        </div>
      </div>

      <button className="btn" onClick={calculateROPSingle} disabled={loading || !product}>
        {loading ? 'Calculating...' : 'Calculate Single ROP'}
      </button>

      {error && <div className="result-card danger" style={{ marginTop: '1.5rem' }}>{error}</div>}

      {result && !result.batch && (
        <div className="results">
          <div className={`result-card ${result.status === 'sufficient' ? 'success' : 'danger'}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>Action Required: <span className={`badge ${result.status === 'sufficient' ? 'success' : 'danger'}`}>{result.status === 'sufficient' ? 'Sufficient Stock' : 'Order Now'}</span></span>
            </div>
            
            <div className="grid" style={{ marginTop: '1.5rem' }}>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Reorder Point (ROP)</p>
                <strong>{result.rop} units</strong>
              </div>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Days Until Stockout</p>
                <strong>{result.days_until_stockout < 900 ? result.days_until_stockout + ' days' : 'N/A'}</strong>
              </div>
              <div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Suggested Order Qty</p>
                <strong>{result.order_quantity_suggested} units</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      {result && result.batch && (
        <div className="results">
           <h3>Bulk Restock Analytics</h3>
           
           <div className="sub-card" style={{ marginBottom: '1.5rem', height: '350px' }}>
              <p style={{ fontWeight: 600, marginBottom: '1rem' }}>Restock Velocity (Top 15 Most Urgent)</p>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getBulkChartData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{fontSize: 12}} />
                  <YAxis />
                  <RechartsTooltip cursor={{fill: 'transparent'}} />
                  <Legend />
                  <Bar dataKey="currentStock" name="Current Stock" fill="#9ca3af" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="suggestedOrder" name="Suggested Order Qty" radius={[4, 4, 0, 0]}>
                    {getBulkChartData().map((entry, index) => <Cell key={`cell-${index}`} fill={entry.isDanger ? '#ef4444' : '#10b981'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
           </div>
           
           <div className="sub-card">
              <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '0.5rem 0' }}>Product</th>
                  <th>Status</th>
                  <th>Stockout In</th>
                  <th>Order Qty</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem 0' }}>{r.product}</td>
                    <td><span className={`badge ${r.status === 'sufficient' ? 'success' : 'danger'}`}>{r.status === 'order_now' ? 'Order Now!' : 'Sufficient'}</span></td>
                    <td>{r.days_until_stockout < 900 ? r.days_until_stockout + 'd' : 'Safe'}</td>
                    <td style={{ fontWeight: 600 }}>{r.order_quantity_suggested}</td>
                  </tr>
                ))}
              </tbody>
            </table>
           </div>
        </div>
      )}
    </div>
  );
}
