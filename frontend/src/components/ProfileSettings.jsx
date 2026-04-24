import { useState } from 'react';

export default function ProfileSettings({ user, token, onUpdateUser }) {
  const [formData, setFormData] = useState({
    owner_name: user?.owner_name || '',
    shop_name: user?.shop_name || '',
    location: user?.location || '',
    business_type: user?.business_type || 'Grocery',
    inventory_type: user?.inventory_type || 'durable',
    lead_time_days: user?.lead_time_days || 7,
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/profile/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          lead_time_days: Number(formData.lead_time_days)
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to save profile');
      
      setMessage('Profile updated successfully!');
      
      // Update the parent's user state so the header updates instantly
      onUpdateUser({ ...user, ...formData });
      
      // Clear success message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>⚙️ Manage Business Profile</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Update your business details. These settings allow the AI to give you hyper-personalized market, tax, and inventory advice.
      </p>

      <form onSubmit={handleSave}>
        <div className="grid">
          <div className="form-group">
            <label>Owner Name</label>
            <input name="owner_name" type="text" required value={formData.owner_name} onChange={handleChange} />
          </div>
          
          <div className="form-group">
            <label>Shop Name</label>
            <input name="shop_name" type="text" required value={formData.shop_name} onChange={handleChange} />
          </div>
          
          <div className="form-group">
            <label>Location (City/Region)</label>
            <input name="location" type="text" placeholder="e.g. Mumbai, Maharashtra" value={formData.location} onChange={handleChange} />
          </div>
          
          <div className="form-group">
            <label>Default Vendor Lead Time (Days)</label>
            <input name="lead_time_days" type="number" min="0" value={formData.lead_time_days} onChange={handleChange} />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)", display: "block', marginTop: '0.25rem' }}>
              Used locally for Inventory Replenishment calculations.
            </span>
          </div>
          
          <div className="form-group">
            <label>Business Type</label>
            <select name="business_type" value={formData.business_type} onChange={handleChange}>
              {['Grocery','Dairy','Hardware','Pharmacy','Electronics','Clothing','Restaurant','Services'].map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label>Inventory Type</label>
            <select name="inventory_type" value={formData.inventory_type} onChange={handleChange}>
              <option value="durable">Durable (Long shelf life, e.g. Hardware/Electronics)</option>
              <option value="perishable">Perishable (Short shelf life, e.g. Dairy/Produce)</option>
              <option value="seasonal">Seasonal (e.g. Clothing/Holiday items)</option>
              <option value="service-based">Service Based (No physical inventory)</option>
            </select>
          </div>
        </div>

        {error && <div className="result-card danger" style={{ marginTop: '1rem', padding: '0.75rem 1rem' }}>{error}</div>}
        {message && <div className="result-card success" style={{ marginTop: '1rem', padding: '0.75rem 1rem' }}>{message}</div>}

        <button type="submit" className="btn" disabled={loading} style={{ marginTop: '1rem' }}>
          {loading ? 'Saving...' : 'Update Profile'}
        </button>
      </form>
    </div>
  );
}
