"""
Agente de Análisis Financiero

Role:
  - Analiza datos reales de ingresos/gastos
  - Detecta riesgos y oportunidades
  - Sugiere acciones
  - NUNCA registra datos (eso lo hace el parser_agent)
  - Responde en lenguaje natural, listo para WhatsApp/Telegram
"""

import json
import os
from openai import OpenAI

from services.financial_service import get_resumen, get_ultimos_movimientos


def _get_client():
    """Retorna cliente OpenAI o None si no hay API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


SYSTEM_PROMPT = """
Eres el Asesor Financiero Senior de ChatPyme. Tu misión es transformar números fríos en decisiones estratégicas para que las Mipymes no mueran por falta de caja.

Tu Enfoque:

Prioridad de Caja: El flujo de caja es el rey. Si el balance es negativo o los gastos crecen más rápido que las ventas, esa es tu primera frase.

Análisis de Tendencias: No solo digas cuánto se gastó, intenta comparar (ej. "Tus gastos en proveedores subieron respecto a la semana pasada").

Acciones de Supervivencia: Si detectas peligro, sugiere ajustar precios, reducir inventario de baja rotación o controlar gastos hormiga.

Estructura de Respuesta:

El Diagnóstico (La Verdad Desnuda): Empieza con la salud del negocio. "Tienes un flujo de caja saludable" o "Cuidado: estás gastando más de lo que ingresas".

El "Por Qué": Identifica el culpable (ej. "La categoría de insumos representa el 60% de tus salidas").

La Receta: Una acción concreta. "Podrías reducir el volumen de compra de X esta semana para recuperar liquidez".

Reglas de Oro:

Personalidad: Profesional, cercano y directo. Usa "tú" o "vos".

Cero Basura Técnica: Prohibido hablar de "pasivos corrientes" o "EBITDA" a menos que lo expliques como "lo que te queda libre".

Brevedad: Máximo 3 párrafos. El usuario está en un chat, no leyendo un informe contable.

Si no hay datos:

Di: "Todavía no tengo suficientes registros para darte un análisis profundo. Si anotamos tus ventas y gastos de hoy, podré decirte cómo va tu margen".
"""

FALLBACK_PROMPT = """
Si hay riesgos o datos inconsistentes:
- No digas "error"
- Guía: "No tengo suficientes datos para analizar. 
  Registra algunos movimientos y te daré un análisis completo"
"""


def obtener_estado_financiero(context: str = "") -> dict:
    """Analiza la situación financiera usando datos reales + OpenAI.
    
    Args:
        context: Historial de conversación para referencia
    
    Retorna dict con llave "data" para compatibilidad con orchestrator.
    """
    
    # Obtener datos reales
    resumen = get_resumen(dias=30)
    ultimos = get_ultimos_movimientos(cantidad=10)
    
    # Contexto para el modelo
    CONTEXT = f"""
    DATOS REALES PARA ANALIZAR
    
    Período: últimos 30 días
    
    Totales:
    - Ingresos: ${resumen['ingresos_total']:,.2f}
    - Gastos: ${resumen['gastos_total']:,.2f}
    - Balance: ${resumen['balance']:,.2f}
    
    Ingresos por categoría:
    {json.dumps(resumen['ingresos_por_categoria'], ensure_ascii=False, indent=2)}
    
    Gastos por categoría:
    {json.dumps(resumen['gastos_por_categoria'], ensure_ascii=False, indent=2)}
    
    Últimos movimientos:
    {json.dumps([dict(m) for m in ultimos], ensure_ascii=False, indent=2, default=str)}
    
    Total de movimientos registrados: {resumen['cantidad_movimientos']}
    """
    
    client = _get_client()
    
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": CONTEXT},
                    {"role": "user", "content": "Analiza mi situación financiera"}
                ],
                temperature=0.6
            )
            
            mensaje = response.choices[0].message.content
            if mensaje and mensaje.strip():
                return {"data": mensaje.strip()}
                
        except Exception:
            pass
        
        # Recovery fallback
        try:
            recovery = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": FALLBACK_PROMPT},
                    {"role": "system", "content": CONTEXT},
                    {"role": "user", "content": "Ayúdame a entender mis finanzas"}
                ],
                temperature=0.6
            )
            
            msg = recovery.choices[0].message.content or _fallback_analysis(resumen)
            return {"data": msg}
            
        except Exception:
            pass
    
    return {"data": _fallback_analysis(resumen)}


def _fallback_analysis(resumen: dict) -> str:
    """Análisis local cuando OpenAI no está disponible."""
    ingresos = resumen['ingresos_total']
    gastos = resumen['gastos_total']
    balance = resumen['balance']
    
    if ingresos == 0:
        return "Aún no tienes ingresos registrados. Registra tus primeros movimientos para que te ayude a analizar."
    
    if gastos == 0:
        return f"En los últimos 30 días facturaste ${ingresos:,.2f} sin registrar gastos. ¿Eso es correcto?"
    
    respuesta = f"En los últimos 30 días:\n"
    respuesta += f"- Facturaste ${ingresos:,.2f}\n"
    respuesta += f"- Gastaste ${gastos:,.2f}\n"
    respuesta += f"- Tu balance es ${balance:,.2f}\n"
    
    if balance < 0:
        respuesta += "\nALERTA: Gastaste más de lo que ganaste este mes."
    elif balance > 0:
        respuesta += f"\nPositivo: Tuviste un superávit de ${balance:,.2f}"
    
    respuesta += "\nRegistra más movimientos para que te ayude a identificar patrones."
    
    return respuesta

