"""
app.py — ChatPyme Backend
Punto de entrada de la aplicación FastAPI.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db, seed_db_from_test
from routes.inventory_routes import router as inventory_router
from routes.financial_routes import router as financial_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ─────────────────────────────────────────────
# LIFESPAN (reemplaza el @app.on_event deprecado)
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización al arranque y limpieza al cierre."""
    # STARTUP
    logger.info("🚀 Iniciando ChatPyme...")
    init_db()
    logger.info("✅ Base de datos inicializada")

    if os.getenv("ENV") == "development":
        # El seed ya NO se ejecuta globalmente.
        # Se ejecuta por usuario la primera vez que interactúa con el bot.
        # Si quieres forzar seed para tu propio Telegram ID en dev, descomenta:
        # from database.database import seed_db_from_test, get_or_create_user
        # seed_db_from_test(user_id=get_or_create_user("TU_TELEGRAM_ID_AQUI"))
        logger.info("🌱 Modo desarrollo activo (seed por usuario, no global)")

    yield  # La app está corriendo

    # SHUTDOWN
    logger.info("🛑 ChatPyme cerrando...")


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

ENV = os.getenv("ENV", "production")

app = FastAPI(
    title="ChatPyme API",
    description="ERP conversacional para Mipymes colombianas 🤖",
    version="1.0.0",
    # Deshabilitar docs en producción
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

# En producción, reemplaza "*" con el dominio de tu frontend real
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# ROUTERS ESTABLES (siempre presentes en el MVP)
# ─────────────────────────────────────────────

app.include_router(inventory_router)
app.include_router(financial_router)


# ─────────────────────────────────────────────
# ROUTERS OPCIONALES (se cargan si existen)
# ─────────────────────────────────────────────

_optional_routers = [
    "routes.auth_routes",
    "routes.users_routes",
    "routes.registro_routes",
    "routes.alerts_routes",
]

for module_name in _optional_routers:
    try:
        import importlib
        mod = importlib.import_module(module_name)
        if hasattr(mod, "router"):
            app.include_router(mod.router)
            logger.info(f"✅ Router cargado: {module_name}")
    except ModuleNotFoundError:
        pass  # Módulo no existe aún, ignorar silenciosamente
    except Exception as e:
        logger.warning(f"⚠️  No se pudo cargar {module_name}: {e}")


# ─────────────────────────────────────────────
# ENDPOINTS BASE
# ─────────────────────────────────────────────

@app.get("/", tags=["health"])
def health():
    return {
        "status": "ChatPyme Online 🤖",
        "env": ENV,
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
def health_check():
    """Endpoint para Railway/GCP health checks."""
    try:
        from database.database import get_db
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }


# ─────────────────────────────────────────────
# ENTRYPOINT LOCAL
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=ENV == "development",
    )