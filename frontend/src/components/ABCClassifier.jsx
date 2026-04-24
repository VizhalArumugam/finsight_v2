import { useState, useRef, useEffect } from 'react';
import Papa from 'papaparse';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function ABCClassifier({ businessType, token }) {
  const fileInputRef = useRef(null);
  const COLORS = ['#10b981', '#f59e0b', '#ef4444']; // Success green, warning yellow, danger red

  const getProductsForType = (type) => {
    const map = {
      'Dairy': ['Toned Milk 500ml', 'Full Cream Milk 500ml', 'Curd 400g', 'Paneer 200g'],
      'Grocery': ['Atta 5kg', 'Rice 5kg', 'Sunflower Oil 1L', 'Sugar 1kg', 'Toor Dal 1kg'],
      'Hardware': ['Fevicol 200g', 'Asian Paints 1L', 'PVC Pipe 1m', 'Hammer 500g'],
      'Pharmacy': ['Paracetamol strip', 'Sanitizer 100ml']
    };
    return map[type] || ['Generic Product 1', 'Generic Product 2', 'Generic Product 3'];
  };

  const [products, setProducts] = useState([]);
  
  useEffect(() => {
      const initialProducts = getProductsForType(businessType).map(p => ({
        name: p, monthly_sales_qty: 0, unit_price: 0
      }));
      setProducts(initialProducts);
  }, [businessType]);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const updateProduct = (i, field, value) => {
    const newP = [...products];
    newP[i][field] = value;
    setProducts(newP);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const parsed = results.data.map((row, i) => ({
          name: row.name || row['Product Name'] || row.item || `Item ${i+1}`,
          monthly_sales_qty: Number(row.monthly_sales_qty || row['Sold Qty'] || row.qty || 0),
          unit_price: Number(row.unit_price || row['Unit Price'] || row.price || 0)
        }));
        setProducts(parsed);
      },
      error: (err) => {
        setError(`Failed to parse CSV: ${err.message}`);
      }
    });
    // reset input
    e.target.value = null;
  };

  const classify = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/abc/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ products })
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

  // Recharts preparation
  const getPieData = () => {
    if (!result) return [];
    return [
      { name: 'Class A', value: result.summary_counts.A },
      { name: 'Class B', value: result.summary_counts.B },
      { name: 'Class C', value: result.summary_counts.C },
    ].filter(d => d.value > 0);
  };

  const getBarData = () => {
    if (!result) return [];
    // Show top 10 products
    return result.products.slice(0, 10).map(p => ({
      name: p.name.length > 15 ? p.name.substring(0, 15) + '...' : p.name,
      revenue: p.revenue,
      fill: p.class === 'A' ? COLORS[0] : p.class === 'B' ? COLORS[1] : COLORS[2]
    }));
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>ABC Inventory Analytics</h2>
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
            >
              Upload CSV Sheet
            </button>
        </div>
      </div>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', marginTop: '0.5rem' }}>
        Identify your most important products (Class A) based on revenue contribution. Enter data manually or bulk-upload a CSV file (headers: `name`, `qty`, `price`).
      </p>

      <div className="sub-card" style={{ maxHeight: products.length > 10 ? '400px' : 'auto', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          <span>Product Name</span><span>Monthly Sold Qty</span><span>Unit Price (₹)</span>
        </div>
        {products.map((p, i) => (
          <div key={i} className="dynamic-row">
            <input type="text" value={p.name} onChange={e => updateProduct(i, 'name', e.target.value)} />
            <input type="number" value={p.monthly_sales_qty || ''} onChange={e => updateProduct(i, 'monthly_sales_qty', e.target.value)} placeholder="0" />
            <input type="number" value={p.unit_price || ''} onChange={e => updateProduct(i, 'unit_price', e.target.value)} placeholder="0" />
          </div>
        ))}
      </div>

      <button className="btn" onClick={classify} disabled={loading || products.length === 0}>
        {loading ? 'Classifying Data...' : 'Run ABC Analysis'}
      </button>

      {error && <div className="result-card danger" style={{ marginTop: '1.5rem' }}>{error}</div>}

      {result && (
        <div className="results">
          <h3>Analytics Dashboard</h3>
          
          <div className="grid" style={{ marginBottom: '1.5rem' }}>
            <div className="sub-card">
               <p style={{ fontWeight: 600, marginBottom: '1rem' }}>Overall Revenue</p>
               <h2 style={{ color: 'var(--primary-color)', fontSize: '2.5rem' }}>₹{result.total_revenue.toLocaleString()}</h2>
               <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Class A items drive ~70% of total revenue. Ensure these are never out of stock.</p>
            </div>
            
            <div className="sub-card" style={{ height: '250px' }}>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Class Distribution</p>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={getPieData()} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} label>
                    {getPieData().map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="sub-card" style={{ marginBottom: '1.5rem', height: '300px' }}>
             <p style={{ fontWeight: 600, marginBottom: '1rem' }}>Top Revenue Drivers</p>
             <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getBarData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{fontSize: 12}} />
                  <YAxis />
                  <RechartsTooltip cursor={{fill: 'transparent'}} />
                  <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                    {getBarData().map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
             </ResponsiveContainer>
          </div>

          <div className="sub-card">
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '0.5rem 0' }}>Product</th>
                  <th>Revenue Generated</th>
                  <th>Tier</th>
                </tr>
              </thead>
              <tbody>
                {result.products.map(p => (
                  <tr key={p.name} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem 0' }}>{p.name}</td>
                    <td>₹{p.revenue.toLocaleString()}</td>
                    <td>
                      <span className={`badge ${p.class === 'A' ? 'success' : p.class === 'B' ? 'warning' : 'danger'}`}>Class {p.class}</span>
                    </td>
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
