import React, { useState, useEffect } from 'react';
import '../styles/Invoices.css';

export default function Invoices() {
  const [movimientos, setMovimientos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroTipo, setFiltroTipo] = useState('todos');
  const [filtroCategoria, setFiltroCategoria] = useState('todas');
  const [categorias, setCategorias] = useState([]);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

  useEffect(() => {
    fetchMovimientos();
  }, []);

  const fetchMovimientos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/finanzas/movimientos?limit=100`);
      const data = await response.json();
      
      setMovimientos(data.movimientos || []);
      
      // Extraer categorías únicas
      const cats = [...new Set(data.movimientos.map(m => m.categoria))];
      setCategorias(cats.sort());
    } catch (error) {
      console.error('Error fetching movimientos:', error);
    } finally {
      setLoading(false);
    }
  };

  const movimientosFiltrados = movimientos.filter(m => {
    const cumpleTipo = filtroTipo === 'todos' || m.tipo === filtroTipo;
    const cumpleCategoria = filtroCategoria === 'todas' || m.categoria === filtroCategoria;
    return cumpleTipo && cumpleCategoria;
  });

  const obtenerIcono = (tipo) => {
    return tipo === 'ingreso' ? '📥' : '📤';
  };

  const obtenerColor = (tipo) => {
    return tipo === 'ingreso' ? 'ingreso' : 'gasto';
  };

  const formatearFecha = (fechaStr) => {
    if (!fechaStr) return 'Sin fecha';
    const fecha = new Date(fechaStr);
    return fecha.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return <div className="inv-loading">Cargando facturas...</div>;
  }

  return (
    <div className="invoices-container">
      <div className="invoices-header">
        <h1 className="invoices-title">🧾 Registro de Movimientos</h1>
        <p className="invoices-subtitle">Historial completo de ingresos y gastos</p>
      </div>

      {/* Toolbar de filtros */}
      <div className="invoices-toolbar">
        <div className="filter-group">
          <label>Tipo</label>
          <select 
            value={filtroTipo} 
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="filter-select"
          >
            <option value="todos">Todos</option>
            <option value="ingreso">Ingresos</option>
            <option value="gasto">Gastos</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Categoría</label>
          <select 
            value={filtroCategoria} 
            onChange={(e) => setFiltroCategoria(e.target.value)}
            className="filter-select"
          >
            <option value="todas">Todas</option>
            {categorias.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="filter-stats">
          <div className="stat-item">
            <span className="stat-label">Total registros</span>
            <span className="stat-value">{movimientosFiltrados.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total ingresos</span>
            <span className="stat-value ingreso">
              ${movimientosFiltrados
                .filter(m => m.tipo === 'ingreso')
                .reduce((sum, m) => sum + m.monto, 0)
                .toFixed(2)}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total gastos</span>
            <span className="stat-value gasto">
              ${movimientosFiltrados
                .filter(m => m.tipo === 'gasto')
                .reduce((sum, m) => sum + m.monto, 0)
                .toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Lista de movimientos */}
      <div className="invoices-list">
        {movimientosFiltrados.length === 0 ? (
          <div className="invoices-empty">
            <p>📭 No hay movimientos que coincidan con los filtros</p>
          </div>
        ) : (
          <div className="movements-grid">
            {movimientosFiltrados.map((mov) => (
              <div 
                key={mov.id} 
                className={`movement-card ${obtenerColor(mov.tipo)}`}
              >
                <div className="card-header">
                  <div className="card-icon">{obtenerIcono(mov.tipo)}</div>
                  <div className="card-title-section">
                    <h3 className="card-category">{mov.categoria}</h3>
                    <p className="card-description">{mov.descripcion || 'Sin descripción'}</p>
                  </div>
                </div>

                <div className="card-body">
                  <div className="monto-section">
                    <span className={`monto ${obtenerColor(mov.tipo)}`}>
                      {mov.tipo === 'ingreso' ? '+' : '-'}${mov.monto.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="card-footer">
                  <span className="fecha-badge">
                    📅 {formatearFecha(mov.fecha)}
                  </span>
                  <span className={`tipo-badge ${mov.tipo}`}>
                    {mov.tipo === 'ingreso' ? 'Ingreso' : 'Gasto'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
