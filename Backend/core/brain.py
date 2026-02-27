from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Ahora sí, creamos el cliente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
Eres el cerebro de un asistente inteligente para emprendedores.

Tu trabajo es decidir qué debe hacer el sistema con el mensaje del usuario.

Debes responder SOLO en JSON con este formato:

{
  "intent": "registro | resumen | inventario | conversacion"
}

Reglas de Clasificación (en orden de prioridad):

1. INVENTARIO → SIEMPRE si menciona:
   - Agregar/añadir/insertar producto
   - Stock/inventario/productos
   - Rellenar/cargar inventario
   - "Qué tengo", "cómo está el inventario"
   Ej: "Agregar Laptop", "Añadir 10 unidades de X", "Stock bajo"

2. RESUMEN → Si pregunta por situación financiera:
   - "Cómo voy", "cuánto he gastado", "dame mi balance"
   - Estado financiero, ingresos, gastos totales

3. REGISTRO → Si reporta transacción ECONÓMICA (NO INVENTARIO):
   - "Compré tela", "Vendí 2 gorras", "Pagaron 500"
   - Operación de dinero que NO sea inventario
   - No incluyas aquí lo que menciona stock/productos

4. CONVERSACIÓN → Todo lo demás:
   - "Hola", "Gracias", "Qué eres", social o exploratorio

IMPORTANTE:
- Si hay duda entre INVENTARIO y REGISTRO: elige INVENTARIO
- No inventes otros intents
- No respondas texto, solo JSON
- El "intent" es CASO SENSIBLE
"""

def decidir_intencion(texto):
    """Decide la intención del usuario con detección local primero."""
    
    texto_lower = texto.lower()
    
    # 1. - DETECCION LOCAL

    # INVENTARIO
    if any(palabra in texto_lower for palabra in 
           ["agregar", "añadir", "crear producto", "insertar", "stock", 
            "inventario", "productos", "rellenar", "cargar prueba"]):
        return "inventario"
    
    # FINANZA 
    if any(palabra in texto_lower for palabra in 
           ["cómo voy", "cuánto he", "mi balance", "estado financiero", 
            "ingresos", "gastos", "balance", "finanzas", "dinero", "plata",
            "ganancias", "pérdidas", "perdidas"]):
        return "resumen"
    
    # REGISTRO
    if any(palabra in texto_lower for palabra in 
           ["compré", "compre", "vendí", "vendi", "gasté", "gaste", 
            "pagué", "pagué", "cobré", "cobre"]):
        return "registro"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texto}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    import json
    try:
        return json.loads(content)["intent"]
    except:
        return "conversacion"