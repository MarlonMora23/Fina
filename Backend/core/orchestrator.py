from agents.conversacional_agent import conversar
from agents.inventory_agent import inventoryAgent
from agents.financial_agent import obtener_estado_financiero
from agents.parser_agent import parserAgent
from core.conversation_history import get_history


def ejecutar_accion(intent, texto):
    """Ejecuta la acción según el intent y mantiene historial."""
    
    historial = get_history()
    historial.add_user_message(texto)
    
    if intent == "registro":
        data = parserAgent(texto, context=historial.get_context())
        respuesta = data.get("message", "Movimiento registrado")
        historial.add_agent_response("ParserAgent", respuesta)
        return {
            "type": "registro",
            "data": data,
            "message": respuesta
        }

    if intent == "resumen":
        data = obtener_estado_financiero(context=historial.get_context())
        respuesta = data.get("data", data.get("message", "Análisis financiero"))
        historial.add_agent_response("FinancialAgent", respuesta[:100])  # Guardar resumen
        return {
            "type": "resumen",
            "data": data["data"] if isinstance(data, dict) and "data" in data else data,
            "message": respuesta
        }

    if intent == "inventario":
        respuesta = inventoryAgent(texto, context=historial.get_context())
        
        if not respuesta or not respuesta.strip():
            respuesta = (
                "Revisé tu inventario, pero no pude generar el análisis en este momento. "
                "¿Quieres que lo intente de nuevo?"
            )
        
        historial.add_agent_response("InventoryAgent", respuesta[:100])
        return {
            "type": "inventario",
            "message": respuesta
        }
        
    if intent == "conversacion":
        respuesta = conversar(texto, context=historial.get_context())
        historial.add_agent_response("ConversationalAgent", respuesta)
        return {
            "type": "conversacion",
            "message": respuesta
        }