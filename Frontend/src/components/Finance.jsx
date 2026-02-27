import React, { useState, useEffect } from 'react';
import '../styles/Finance.css';

export default function Finance() {
  const [resumen, setResumen] = useState(null);
  const [analisis, setAnalisis] = useState(null);
  const [movimientos, setMovimientos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    tipo: 'ingreso',
    monto: '',
    categoria: 'Ventas',
    descripcion: '',
  });

  const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

  // Cargar datos al montar el componente
  useEffect(() => {
    fetchFinancialData();
  }, []);

  const fetchFinancialData = async () => {
    setLoading(true);
    try {
      const [resumenRes, analisisRes, movimientosRes] = await Promise.all([
        fetch(`${API_BASE}/finanzas/resumen`),
        fetch(`${API_BASE}/finanzas/analisis`),
        fetch(`${API_BASE}/finanzas/movimientos?limit=10`),
      ]);

      const resumenData = await resumenRes.json();
      const analisisData = await analisisRes.json();
      const movimientosData = await movimientosRes.json();

      setResumen(resumenData);
      setAnalisis(analisisData);
      setMovimientos(movimientosData.movimientos || []);
    } catch (error) {
      console.error('Error fetching financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmitMovimiento = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/finanzas/movimiento`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          monto: parseFloat(formData.monto),
        }),
      });

      const result = await response.json();
      if (result.success) {
        setFormData({
          tipo: 'ingreso',
          monto: '',
          categoria: 'Ventas',
          descripcion: '',
        });
        fetchFinancialData();
      }
    } catch (error) {
      console.error('Error registering movement:', error);
    }
  };

  if (loading) {
    return <div className="fin-loading">Cargando datos financieros...</div>;
  }

  // Colores basados en balance
  const getBalanceColor = () => {
    if (!resumen) return '#999';
    if (resumen.balance > 0) return '#10b981';
    if (resumen.balance < 0) return '#ef4444';
    return '#f59e0b';
  };

  return (
    <div className="fin-container">
      <h1 className="fin-title">💰 Finanzas</h1>

      {/* Cards de Resumen */}
      <div className="fin-Summary">
        <div className="fin-card fin-card--ingresos">
          <div className="fin-card__icon">📥</div>
          <div className="fin-card__content">
            <h3>Ingresos</h3>
            <p className="fin-card__amount">${resumen?.ingresos_total?.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</p>
          </div>
        </div>

        <div className="fin-card fin-card--gastos">
          <div className="fin-card__icon">📤</div>
          <div className="fin-card__content">
            <h3>Gastos</h3>
            <p className="fin-card__amount">${resumen?.gastos_total?.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</p>
          </div>
        </div>

        <div className="fin-card fin-card--balance" style={{ borderLeftColor: getBalanceColor() }}>
          <div className="fin-card__icon">📊</div>
          <div className="fin-card__content">
            <h3>Balance</h3>
            <p className="fin-card__amount" style={{ color: getBalanceColor() }}>
              ${resumen?.balance?.toLocaleString('es-ES', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Análisis del Agente */}
      {analisis?.data && (
        <div className="fin-analysis">
          <h2>🧠 Análisis Financiero</h2>
          <div className="fin-analysis__content">
            <p>{analisis.data}</p>
          </div>
        </div>
      )}

      {/* Formulario de Registro */}
      <div className="fin-form-section">
        <h2>➕ Registrar Movimiento</h2>
        <form onSubmit={handleSubmitMovimiento} className="fin-form">
          <div className="fin-form__row">
            <div className="fin-form__group">
              <label>Tipo</label>
              <select 
                name="tipo" 
                value={formData.tipo} 
                onChange={handleFormChange}
                className="fin-form__input"
              >
                <option value="ingreso">Ingreso</option>
                <option value="gasto">Gasto</option>
              </select>
            </div>
            <div className="fin-form__group">
              <label>Monto</label>
              <input 
                type="number" 
                name="monto" 
                value={formData.monto} 
                onChange={handleFormChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                required
                className="fin-form__input"
              />
            </div>
          </div>

          <div className="fin-form__row">
            <div className="fin-form__group">
              <label>Categoría</label>
              <select 
                name="categoria" 
                value={formData.categoria} 
                onChange={handleFormChange}
                className="fin-form__input"
              >
                <option value="Ventas">Ventas</option>
                <option value="Marketing">Marketing</option>
                <option value="Salarios">Salarios</option>
                <option value="Utilities">Utilities</option>
                <option value="Materiales">Materiales</option>
                <option value="Consultoría">Consultoría</option>
                <option value="Servicios">Servicios</option>
                <option value="Otros">Otros</option>
              </select>
            </div>
            <div className="fin-form__group">
              <label>Descripción (opcional)</label>
              <input 
                type="text" 
                name="descripcion" 
                value={formData.descripcion} 
                onChange={handleFormChange}
                placeholder="Descripción del movimiento"
                className="fin-form__input"
              />
            </div>
          </div>

          <button type="submit" className="fin-form__submit">
            ✅ Registrar Movimiento
          </button>
        </form>
      </div>

      {/* Tabla de Movimientos */}
      <div className="fin-movements">
        <h2>📋 Últimos Movimientos</h2>
        {movimientos.length > 0 ? (
          <div className="fin-movements__list">
            {movimientos.map((mov, idx) => (
              <div 
                key={idx} 
                className={`fin-movement fin-movement--${mov.tipo}`}
              >
                <div className="fin-movement__icon">
                  {mov.tipo === 'ingreso' ? '📥' : '📤'}
                </div>
                <div className="fin-movement__content">
                  <h4>{mov.categoria}</h4>
                  <p>{mov.descripcion || 'Sin descripción'}</p>
                  <small>{new Date(mov.fecha).toLocaleDateString('es-ES')}</small>
                </div>
                <div className={`fin-movement__amount fin-movement__amount--${mov.tipo}`}>
                  {mov.tipo === 'ingreso' ? '+' : '-'}${mov.monto.toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="fin-empty">No hay movimientos registrados</p>
        )}
      </div>

      {/* Categorías */}
      {(resumen?.ingresos_por_categoria || resumen?.gastos_por_categoria) && (
        <div className="fin-categories">
          {resumen?.ingresos_por_categoria && Object.keys(resumen.ingresos_por_categoria).length > 0 && (
            <div className="fin-category-section">
              <h3>💵 Ingresos por Categoría</h3>
              <ul>
                {Object.entries(resumen.ingresos_por_categoria).map(([cat, monto]) => (
                  <li key={cat}>
                    <span>{cat}</span>
                    <span>${monto.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {resumen?.gastos_por_categoria && Object.keys(resumen.gastos_por_categoria).length > 0 && (
            <div className="fin-category-section">
              <h3>💳 Gastos por Categoría</h3>
              <ul>
                {Object.entries(resumen.gastos_por_categoria).map(([cat, monto]) => (
                  <li key={cat}>
                    <span>{cat}</span>
                    <span>${monto.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
