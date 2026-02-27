"""
database/database.py

Base de datos SQLite para ChatPyme.
Cada usuario tiene su propio espacio de datos aislado por user_id.
"""

import sqlite3
import json
import logging
from pathlib import Path

DB_PATH = Path(__file__).parent / "inventario.db"
logger = logging.getLogger(__name__)


def get_db() -> sqlite3.Connection:
    """Retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Activar foreign keys para integridad referencial
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Crea todas las tablas si no existen. Seguro de llamar múltiples veces."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Usuarios ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT NOT NULL UNIQUE,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Inventario (aislado por user_id) ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            producto    TEXT NOT NULL,
            categoria   TEXT DEFAULT 'General',
            stock_actual  INTEGER DEFAULT 0,
            stock_minimo  INTEGER DEFAULT 0,
            stock_maximo  INTEGER,
            precio      REAL DEFAULT 0,
            sku         TEXT,
            ultimo_movimiento_dias INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, producto)
        )
    """)

    # ── Movimientos financieros (aislados por user_id) ────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tipo        TEXT NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
            monto       REAL NOT NULL,
            categoria   TEXT NOT NULL,
            descripcion TEXT,
            fecha       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Auditoría (opcional, para debug) ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT NOT NULL,
            payload    TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Migrar BD existente si le faltan columnas
    _migrate(cursor, conn)

    conn.close()


def _migrate(cursor, conn):
    """
    Agrega columnas faltantes a tablas existentes (para BDs antiguas sin user_id).
    SQLite no soporta ALTER TABLE ADD COLUMN con restricciones, así que
    agregamos la columna nullable y luego actualizamos los registros huérfanos.
    """
    # products: agregar user_id si no existe
    cols_products = {row[1] for row in cursor.execute("PRAGMA table_info(products)")}
    if "user_id" not in cols_products:
        logger.warning("[db] Migrando tabla 'products': agregando user_id")
        cursor.execute("ALTER TABLE products ADD COLUMN user_id INTEGER")
        # Asignar un user_id=0 temporal a los registros huérfanos
        cursor.execute("UPDATE products SET user_id = 0 WHERE user_id IS NULL")
        conn.commit()

    # movimientos: agregar user_id si no existe
    cols_mov = {row[1] for row in cursor.execute("PRAGMA table_info(movimientos)")}
    if "user_id" not in cols_mov:
        logger.warning("[db] Migrando tabla 'movimientos': agregando user_id")
        cursor.execute("ALTER TABLE movimientos ADD COLUMN user_id INTEGER")
        cursor.execute("UPDATE movimientos SET user_id = 0 WHERE user_id IS NULL")
        conn.commit()


def get_or_create_user(telegram_id: str) -> int:
    """
    Retorna el user_id interno para el telegram_id dado.
    Si el usuario no existe, lo crea.
    
    Args:
        telegram_id: ID numérico de Telegram como string.
    
    Returns:
        user_id (int) — nunca retorna None.
    
    Raises:
        RuntimeError si no puede crear/encontrar el usuario.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Buscar usuario existente
        cursor.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (str(telegram_id),)
        )
        row = cursor.fetchone()
        if row:
            return row["id"]

        # Crear nuevo usuario
        cursor.execute(
            "INSERT INTO users (telegram_id) VALUES (?)", (str(telegram_id),)
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"[db] Nuevo usuario registrado: telegram_id={telegram_id}, user_id={user_id}")
        return user_id

    except Exception as e:
        logger.error(f"[db] Error en get_or_create_user({telegram_id}): {e}")
        raise RuntimeError(f"No se pudo obtener/crear el usuario: {e}") from e
    finally:
        conn.close()


def seed_db_from_test(user_id: int = None):
    """
    Carga datos de prueba SOLO para un usuario específico.
    Si user_id es None, no hace nada (evita contaminar datos globales).
    Solo inserta si el usuario aún no tiene productos.
    """
    if user_id is None:
        logger.debug("[db] seed_db_from_test ignorado: no se proporcionó user_id")
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) as count FROM products WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone()["count"] > 0:
        conn.close()
        logger.debug(f"[db] Seed omitido: user_id={user_id} ya tiene productos")
        return

    productos_iniciales = [
        # (producto, categoria, stock_actual, stock_minimo, stock_maximo, precio)
        ("Camiseta Básica",       "Ropa",        45, 10, 100, 15.99),
        ("Pantalón Jean",         "Ropa",        28,  5,  50, 49.99),
        ("Remera Estampada",      "Ropa",        32,  8,  60, 22.99),
        ("Sudadera",              "Ropa",        18,  5,  40, 39.99),
        ("Gorra",                 "Accesorios",  35, 10,  80, 18.99),
        ("Cinturón",              "Accesorios",  22,  5,  40, 25.99),
        ("Lentes de Sol",         "Accesorios",  42, 15, 100, 12.99),
        ("Zapatillas Deportivas", "Calzado",     19,  5,  35, 89.99),
        ("Botas",                 "Calzado",     12,  3,  25, 99.99),
        ("Sandalias",             "Calzado",     31, 10,  60, 35.99),
        ("Cable USB",             "Electrónica", 67, 20, 150,  8.99),
        ("Auriculares",           "Electrónica", 24,  5,  50, 34.99),
        ("Jabón",                 "Cosméticos", 120, 30, 250,  3.99),
        ("Champú",                "Cosméticos",  36, 10,  80,  9.99),
    ]

    movimientos_iniciales = [
        ("ingreso", 450.00, "Ventas",           "Venta de camisetas y pantalones"),
        ("ingreso", 320.00, "Ventas",           "Venta de accesorios"),
        ("gasto",   200.00, "Reabastecimiento", "Compra de productos a proveedor"),
        ("gasto",    85.50, "Operación",        "Gastos de local"),
        ("ingreso", 275.00, "Ventas",           "Venta de calzado"),
        ("gasto",   150.00, "Reabastecimiento", "Compra de electrónica"),
    ]

    try:
        for producto, categoria, stock_actual, stock_minimo, stock_maximo, precio in productos_iniciales:
            cursor.execute("""
                INSERT OR IGNORE INTO products
                    (user_id, producto, categoria, stock_actual, stock_minimo, stock_maximo, precio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, producto, categoria, stock_actual, stock_minimo, stock_maximo, precio))

        cursor.execute(
            "SELECT COUNT(*) as count FROM movimientos WHERE user_id = ?", (user_id,)
        )
        if cursor.fetchone()["count"] == 0:
            for tipo, monto, categoria, descripcion in movimientos_iniciales:
                cursor.execute("""
                    INSERT INTO movimientos (user_id, tipo, monto, categoria, descripcion)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, tipo, monto, categoria, descripcion))

        conn.commit()
        logger.info(f"[db] Seed cargado para user_id={user_id}")

    except Exception as e:
        logger.error(f"[db] Error en seed: {e}")
    finally:
        conn.close()


def log_action(user_id: int, action: str, payload: dict = None):
    """Registra una acción en el log de auditoría."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_log (user_id, action, payload) VALUES (?, ?, ?)",
            (user_id, action, json.dumps(payload or {}, default=str))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"[db] audit_log falló (no crítico): {e}")