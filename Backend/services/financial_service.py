from database.database import get_db
from datetime import datetime, timedelta


def add_movimiento(tipo: str, monto: float, categoria: str, descripcion: str = None) -> dict:
    if tipo not in ("ingreso", "gasto"):
        raise ValueError("tipo debe ser 'ingreso' o 'gasto'")
    
    if monto <= 0:
        raise ValueError("monto debe ser positivo")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO movimientos (tipo, monto, categoria, descripcion)
            VALUES (?, ?, ?, ?)
        """, (tipo, monto, categoria, descripcion or ""))
        
        conn.commit()
        
        movimiento_id = cursor.lastrowid
        cursor.execute("SELECT * FROM movimientos WHERE id = ?", (movimiento_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "tipo": row["tipo"],
            "monto": row["monto"],
            "categoria": row["categoria"],
            "descripcion": row["descripcion"],
            "fecha": row["fecha"],
        }
    finally:
        conn.close()


def get_movements(limit: int = None, dias: int = None) -> list:
    """Obtiene movimientos. 
    
    Args:
        limit: cantidad máxima de registros
        dias: últimos N días (si no se especifica, trae todo)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM movimientos"
    params = []
    
    if dias:
        fecha_limite = datetime.now() - timedelta(days=dias)
        query += " WHERE fecha >= ?"
        params.append(fecha_limite.isoformat())
    
    query += " ORDER BY fecha DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_resumen(dias: int = 30) -> dict:
    """Retorna resumen financiero de los últimos N días."""
    conn = get_db()
    cursor = conn.cursor()
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    # Total ingresos
    cursor.execute("""
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM movimientos 
        WHERE tipo = 'ingreso' AND fecha >= ?
    """, (fecha_limite.isoformat(),))
    ingresos = cursor.fetchone()["total"]
    
    # Total gastos
    cursor.execute("""
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM movimientos 
        WHERE tipo = 'gasto' AND fecha >= ?
    """, (fecha_limite.isoformat(),))
    gastos = cursor.fetchone()["total"]
    
    # Ingresos por categoría
    cursor.execute("""
        SELECT categoria, SUM(monto) as total
        FROM movimientos
        WHERE tipo = 'ingreso' AND fecha >= ?
        GROUP BY categoria
        ORDER BY total DESC
    """, (fecha_limite.isoformat(),))
    ingresos_por_cat = {row["categoria"]: row["total"] for row in cursor.fetchall()}
    
    # Gastos por categoría
    cursor.execute("""
        SELECT categoria, SUM(monto) as total
        FROM movimientos
        WHERE tipo = 'gasto' AND fecha >= ?
        GROUP BY categoria
        ORDER BY total DESC
    """, (fecha_limite.isoformat(),))
    gastos_por_cat = {row["categoria"]: row["total"] for row in cursor.fetchall()}
    
    balance = ingresos - gastos
    
    conn.close()
    
    return {
        "periodo_dias": dias,
        "ingresos_total": round(ingresos, 2),
        "gastos_total": round(gastos, 2),
        "balance": round(balance, 2),
        "ingresos_por_categoria": ingresos_por_cat,
        "gastos_por_categoria": gastos_por_cat,
        "cantidad_movimientos": len(get_movements(dias=dias)),
    }


def get_movimientos_por_categoria(tipo: str, dias: int = 30) -> dict:
    """Retorna movimientos agrupados por categoría (ingreso o gasto)."""
    conn = get_db()
    cursor = conn.cursor()
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    cursor.execute("""
        SELECT categoria, COUNT(*) as cantidad, SUM(monto) as total
        FROM movimientos
        WHERE tipo = ? AND fecha >= ?
        GROUP BY categoria
        ORDER BY total DESC
    """, (tipo, fecha_limite.isoformat()))
    
    rows = cursor.fetchall()
    conn.close()
    
    return {row["categoria"]: {"cantidad": row["cantidad"], "total": round(row["total"], 2)} 
            for row in rows}


def get_ultimos_movimientos(cantidad: int = 10) -> list:
    """Retorna los últimos movimientos para contexto del agente."""
    return get_movements(limit=cantidad)
