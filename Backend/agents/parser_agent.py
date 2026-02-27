import json
import re
import os

from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

from services.financial_service import add_movimiento

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


def _get_client():
    """Retorna cliente OpenAI o None."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def parserAgent(message_user: str, context: str = "") -> dict:
    """
    Parsea un mensaje financiero y lo registra en la base de datos.
    
    Args:
        message_user: Mensaje del usuario a parsear
        context: Historial de conversación para referencia
    
    Retorna:
        {
            "success": True/False,
            "message": "Confirmación amigable",
            "tipo": "ingreso|gasto",
            "monto": 1000.00,
            "categoria": "Ventas"
        }
    """
    
    client = _get_client()
    if not client:
        return {
            "success": False,
            "message": "No está configurada la API key de OpenAI. No puedo registrar el movimiento.",
            "error": "OPENAI_API_KEY not set"
        }

    # Prompt para parsear
    prompt = f"""
Extrae información financiera de este mensaje:

"{message_user}"

Responde SOLO en JSON válido con esta estructura:
{{
  "tipo": "ingreso" o "gasto",
  "monto": número positivo,
  "categoria": "nombre de la categoría" (ej: Ventas, Marketing, Salarios),
  "descripcion": "breve descripción" (opcional)
}}

Si el mensaje no contiene información clara:
- tipo: null
- monto: null
- categoria: null
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
        )

        content = response.choices[0].message.content or ""
        cleaned = content.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        parsed = json.loads(cleaned)
        
        tipo = parsed.get("tipo")
        monto = parsed.get("monto")
        categoria = parsed.get("categoria")
        descripcion = parsed.get("descripcion", "")
        
        if not tipo or not monto or not categoria:
            return {
                "success": False,
                "message": "No pude extraer la información financiera del mensaje. Intenta algo como: 'Vendí 2 productos por $500' o 'Gasté $100 en marketing'",
                "tipo": None
            }
        
        # Registrar en BD
        try:
            movimiento = add_movimiento(
                tipo=tipo.lower(),
                monto=float(monto),
                categoria=categoria,
                descripcion=descripcion
            )
            
            tipo_texto = "Ingreso" if tipo.lower() == "ingreso" else "Gasto"
            mensaje = f"✅ {tipo_texto} de ${movimiento['monto']:,.2f} registrado en {movimiento['categoria']}."
            
            return {
                "success": True,
                "message": mensaje,
                "tipo": tipo.lower(),
                "monto": float(monto),
                "categoria": categoria,
                "id_movimiento": movimiento["id"]
            }
            
        except Exception as db_error:
            return {
                "success": False,
                "message": f"Error al guardar el movimiento: {str(db_error)}",
                "tipo": tipo
            }
            
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "No pude procesar el mensaje correctamente. Intenta de nuevo.",
            "error": "JSON parse error"
        }
    except Exception as error:
        return {
            "success": False,
            "message": "Ocurrió un error procesando tu solicitud.",
            "error": str(error),
        }
