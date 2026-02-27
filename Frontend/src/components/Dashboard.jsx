import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ name: '', stock: '', min: '' });

  const mapBackendItem = (item) => {
    const name = item.producto || item.nombre || item.name || 'Sin nombre';
    const category = item.categoria || item.category || 'General';
    const stock = item.stock_actual ?? item.stock ?? 0;
    const min = item.stock_minimo ?? item.min ?? 1;
    const max = item.stock_maximo ?? item.max ?? Math.max(min * 2, stock);
    const sku = item.sku || `SKU-${name.replace(/\s+/g, '_').toUpperCase()}`;
    const price = item.precio ?? item.price ?? 0;

    return {
      name,
      sku,
      category,
      price,
      min,
      max,
      stock,
      trend: item.trend ?? 0,
      status: stock <= min ? 'bajo' : stock >= max ? 'optimo' : 'normal',
    };
  };

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const apiBase = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';
      const res = await fetch(`${apiBase}/inventory`);
      if (!res.ok) throw new Error('Error al obtener inventario');
      const data = await res.json();
      const list = Array.isArray(data) ? data : data.inventario || [];
      setInventory(list.map(mapBackendItem));
    } catch (err) {
      console.error('fetchInventory', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const addItem = async (e) => {
    e.preventDefault();
    const payload = {
      producto: form.name,
      stock_actual: Number(form.stock || 0),
      stock_minimo: Number(form.min || 0),
    };

    try {
      const apiBase = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';
      const res = await fetch(`${apiBase}/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('POST failed');
      await fetchInventory();
      setForm({ name: '', stock: '', min: '' });
    } catch (err) {
      console.error('addItem', err);
    }
  };

  return (
    <div className="inventory-page">
        <header className="main-header">
          <h1>Inventario</h1>
          <div className="user-pill">Pyme Demo</div>
        </header>

        <section className="inventory-wrapper">
          <div className="inventory-toolbar">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input placeholder="Buscar producto, SKU o categoria..." onChange={(e) => {/* noop for now */}} />
            </div>

            <div className="filters">
              <button className="filter-pill active">Todos</button>
              <button className="filter-pill">Bajo Stock</button>
              <button className="filter-pill">Normal</button>
              <button className="filter-pill">Optimo</button>
            </div>
          </div>

          <div className="inventory-card">
            <form onSubmit={addItem} className="inventory-form" style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input type="number" placeholder="Stock" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} />
              <input type="number" placeholder="Min" value={form.min} onChange={(e) => setForm({ ...form, min: e.target.value })} />
              <button type="submit">Agregar</button>
            </form>

            {loading ? (
              <div className="inventory-empty">Cargando inventario...</div>
            ) : (
              <div className="inventory-list">
                {inventory.map((i) => {
                  const fill = Math.round((i.stock / (i.max || Math.max(i.min * 2, i.stock) || 1)) * 100);
                  const isCritical = i.stock <= i.min;
                  const iconClass = isCritical ? 'critical' : i.status === 'optimo' ? 'optimo' : 'normal';
                  const barClass = isCritical ? 'critical' : i.status === 'optimo' ? 'optimo' : 'normal';
                  return (
                    <div key={i.sku} className={`inventory-row inventory-${i.status}`}>
                      <div className="inv-main">
                        <div className={`inv-icon inv-icon-${iconClass}`}>📦</div>
                        <div>
                          <div className="inv-name">{i.name}</div>
                          <div className="inv-meta"><span>{i.sku}</span> • <span>{i.category}</span> {i.price && <span>${i.price.toLocaleString()}</span>}</div>
                          {isCritical && <span className="inv-badge-critical">Crítico</span>}
                        </div>
                      </div>

                      <div className="inv-center">
                        <div className="inv-minmax">Min: {i.min} / Max: {i.max}</div>
                        <div className="inv-bar" aria-hidden>
                          <div className={`inv-bar-fill inv-bar-${barClass}`} style={{ width: `${Math.max(4, Math.min(100, fill))}%` }} />
                        </div>
                      </div>

                      <div className="inv-right">
                        <div className="inv-stock">{i.stock} u.</div>
                        <div className={`inv-trend ${i.trend >= 0 ? 'up' : 'down'}`}>{i.trend >= 0 ? `↑ ${i.trend}` : `↓ ${Math.abs(i.trend)}`}</div>
                      </div>
                    </div>
                  );
                })}

                {inventory.length === 0 && <div className="inventory-empty">No hay productos en el inventario.</div>}
              </div>
            )}
          </div>
        </section>
    </div>
  );
};

export default Dashboard;