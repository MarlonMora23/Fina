import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import Finance from './components/Finance';
import Invoices from './components/Invoices';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('inventario');

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">⚡</div>
        </div>

        <nav className="sidebar-menu">
          <button 
            className={`menu-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`menu-item ${currentView === 'inventario' ? 'active' : ''}`}
            onClick={() => setCurrentView('inventario')}
          >
            📦 Inventario
          </button>
          <button 
            className={`menu-item ${currentView === 'finanzas' ? 'active' : ''}`}
            onClick={() => setCurrentView('finanzas')}
          >
            💰 Finanzas
          </button>
          <button 
            className={`menu-item ${currentView === 'facturas' ? 'active' : ''}`}
            onClick={() => setCurrentView('facturas')}
          >
            🧾 Facturas
          </button>
        </nav>

        <button className="sidebar-logout">Cerrar sesión</button>
      </aside>

      <main className="main-content">
        {currentView === 'inventario' && <Dashboard />}
        {currentView === 'finanzas' && <Finance />}
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'facturas' && <Invoices />}
      </main>
    </div>
  );
}

export default App;
