import json
import sqlite3
from pathlib import Path

TEST_PATH = Path(__file__).parent / "inventory_test.json"


def get_db():
    """Retorna una conexión a la base de datos SQLite."""
    from database.database import get_db as _get_db
    return _get_db()


def init_db():
    """Inicializa la base de datos."""
    from database.database import init_db as _init_db, seed_db_from_test as _seed
    _init_db()
    _seed()


def read_inventory():
    """Lee todo el inventario desde SQLite."""
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    inventario = [dict(row) for row in rows]
    
    return {
        "empresa_id": "pyme_demo_001",
        "inventario": inventario
    }


def write_inventory(data):
    """Sobreescribe el inventario (para compatibilidad, pero usa SQLite)."""
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products")
    
    for item in data.get("inventario", []):
        cursor.execute("""
            INSERT INTO products (
                producto, categoria, stock_actual, stock_minimo,
                ultimo_movimiento_dias, precio, sku, stock_maximo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("producto"),
            item.get("categoria", "General"),
            item.get("stock_actual", 0),
            item.get("stock_minimo", 0),
            item.get("ultimo_movimiento_dias", 0),
            item.get("precio", 0),
            item.get("sku"),
            item.get("stock_maximo"),
        ))
    
    conn.commit()
    conn.close()


def add_product(product):
    """Agrega un producto a la BD SQLite."""
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO products (
                producto, categoria, stock_actual, stock_minimo,
                precio, sku, stock_maximo
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product.get("producto"),
            product.get("categoria", "General"),
            product.get("stock_actual", 0),
            product.get("stock_minimo", 0),
            product.get("precio", 0),
            product.get("sku"),
            product.get("stock_maximo"),
        ))
        
        conn.commit()
        product_id = cursor.lastrowid
        
        product["id"] = product_id
        
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE products SET 
                stock_actual = ?, stock_minimo = ?, precio = ?, stock_maximo = ?
            WHERE producto = ?
        """, (
            product.get("stock_actual", 0),
            product.get("stock_minimo", 0),
            product.get("precio", 0),
            product.get("stock_maximo"),
            product.get("producto"),
        ))
        conn.commit()
    
    conn.close()
    return product