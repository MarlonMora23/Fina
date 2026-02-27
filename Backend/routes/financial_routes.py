from fastapi import APIRouter, Body
from pydantic import BaseModel
from services.financial_service import get_resumen, get_ultimos_movimientos, add_movimiento
from agents.financial_agent import obtener_estado_financiero

router = APIRouter(prefix="/api", tags=["financial"])


class MovimientoCreate(BaseModel):
    tipo: str
    monto: float
    categoria: str
    descripcion: str = None


@router.get("/finanzas/resumen")
def get_financial_summary():
    """Retorna resumen financiero de los últimos 30 días."""
    resumen = get_resumen(dias=30)
    return resumen


@router.get("/finanzas/analisis")
def get_financial_analysis():
    """Retorna análisis del agente financiero."""
    analisis = obtener_estado_financiero()
    return analisis


@router.get("/finanzas/movimientos")
def get_recent_movements(limit: int = 10, dias: int = 30):
    """Retorna movimientos recientes."""
    movimientos = get_ultimos_movimientos(cantidad=limit)
    return {
        "movimientos": [dict(m) for m in movimientos],
        "cantidad": len(movimientos)
    }


@router.post("/finanzas/movimiento")
def create_movement(movimiento: MovimientoCreate):
    """Registra un nuevo movimiento financiero."""
    try:
        resultado = add_movimiento(
            movimiento.tipo,
            movimiento.monto,
            movimiento.categoria,
            movimiento.descripcion
        )
        return {
            "success": True,
            "movimiento": resultado
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
