import json

from openai import OpenAI
import os

from services.inventory_service import read_inventory, add_product, write_inventory, TEST_PATH

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None

# =========================
# SYSTEM PROMPT
# Contexto general + rol
# =========================
SYSTEM_PROMPT = """
Eres el Agente de Análisis de Inventario de ChatPyme, un ERP conversacional
para Mipymes.

Tu rol es actuar como un asesor humano de inventario:
analizas los datos, detectas riesgos y explicas solo lo relevante al usuario.

Cómo razonar internamente:
1. Revisa si el inventario está vacío.
2. Identifica productos con stock bajo (stock_actual <= stock_minimo).
3. Si hay riesgos, menciónalos primero.
4. Si todo está bien, tranquiliza al usuario.
5. Resume, no listes todo.
6. Sugiere una acción útil o pregunta de seguimiento.

Forma de responder:
- Comienza siempre con una frase natural (ej: “Ya revisé tu inventario…”).
- Prioriza lo importante sobre lo completo.
- Usa un tono cercano, profesional y proactivo.
- Nunca devuelvas respuestas vacías ni técnicas.

Reglas:
- No inventes datos.
- No muestres JSON ni estructuras técnicas.
- Responde solo con texto natural, listo para enviarse al usuario.

Ejemplo de estilo:
“En general todo está en orden, aunque hay un producto que convendría reponer pronto…”

"""

# =========================
# RECOVERY PROMPT
# Solo para ambigüedad
# =========================
RECOVERY_PROMPT = """
Si el mensaje del usuario es ambiguo, incompleto o no puedes
realizar un análisis claro:

- No inventes datos
- No digas que ocurrió un error
- Guía al usuario explicando qué tipo de análisis puedes hacer

Ejemplo de respuesta:
"Puedo ayudarte a revisar stock bajo, productos sin movimiento
o posibles faltantes. ¿Qué deseas revisar?"
"""

# =========================
# AGENT FUNCTION
# =========================

def inventoryAgent(user_message: str, context: str = "") -> str:
    """Analiza inventario con contexto de conversación previa.
    
    Args:
        user_message: Mensaje del usuario
        context: Historial de conversación para referencia
    """
    # detectar acciones especiales: agregar producto o rellenar inventario
    text = (user_message or "").strip()
    low = text.lower()

    if any(k in low for k in ("rellenar", "seed", "cargar prueba", "cargar datos", "cargar test")):
        try:
            # leer archivo de prueba y sobrescribir el inventario actual
            with open(TEST_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            write_inventory(data)
            count = len(data.get("inventario", []))
            return f"Inventario rellenado con datos de prueba ({count} productos)."
        except Exception:
            return "No pude rellenar el inventario desde los datos de prueba."

    # Agregar producto: si el usuario pide agregar/añadir/crear
    if any(k in low for k in ("agregar", "añadir", "añade", "crear producto", "insertar")):
        import re
        
        # Parser local robusto (sin modelo)
        def parse_producto_local(msg):
            """Extrae nombre, categoria, stock_actual y stock_minimo del mensaje."""
            msg_low = msg.lower()
            
            result = {
                "producto": None,
                "categoria": "General",
                "stock_actual": 0,
                "stock_minimo": 0,
            }
            
            # Extraer números
            numeros = re.findall(r'\b(\d+)\b', msg)
            
            # Buscar patrones como "stock X", "min Y", "minimo Y"
            stock_match = re.search(r'stock[:\s]+(\d+)', msg_low)
            min_match = re.search(r'(?:min|minimo)[:\s]+(\d+)', msg_low)
            
            if stock_match:
                result["stock_actual"] = int(stock_match.group(1))
            elif numeros:
                result["stock_actual"] = int(numeros[0])
            
            if min_match:
                result["stock_minimo"] = int(min_match.group(1))
            elif len(numeros) > 1:
                result["stock_minimo"] = int(numeros[1])
            
            # Extraer categoría (más flexible)
            cat_match = re.search(r'categor(?:ía|ia)[:\s]+([^,\n]+?)(?:\s*(?:stock|min|precio|sku)|[,]|$)', msg_low)
            if cat_match:
                cat_text = cat_match.group(1).strip()
                # Limpiar números al final
                cat_text = re.sub(r'\s+\d+.*$', '', cat_text).strip()
                if cat_text and len(cat_text) > 2:
                    result["categoria"] = cat_text.title()
            
            # Extraer nombre del producto - MÁS FLEXIBLE
            # Estrategia: buscar todo lo que viene después del verbo hasta coma, "categoria", o número seguido de palabra clave
            name_patterns = [
                # Patrón 1: "Agregar X, categoria Y" o "Agregar X, stock Y"
                r'(?:agregar|añadir|crear|insertar)\s+(?:producto\s+)?(.+?)(?:\s*,\s*(?:categor|stock|min)|$)',
                # Patrón 2: "Agregar X stock Y min Z"
                r'(?:agregar|añadir|crear|insertar)\s+(?:producto\s+)?(.+?)(?:\s+(?:categor|stock|min|precio|sku))',
                # Patrón 3: Lo que sea después del verbo
                r'(?:agregar|añadir|crear|insertar)\s+(?:producto\s+)?(.+?)$'
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, msg_low)
                if name_match:
                    name = name_match.group(1).strip()
                    # Remover números finales (stock, cantidad) pero NO números dentro del nombre
                    # Solo remover si viene como "nombre 50" (número al final suelto)
                    name = re.sub(r'\s+(?:stock|min|categoria|categor|precio|sku).*$', '', name, flags=re.IGNORECASE).strip()
                    
                    name = re.sub(r'\s+\b\d+\s*$', '', name).strip()
                    
                    if name and len(name) > 2: 
                        result["producto"] = name.title()
                        break
            
            return result
        
        # Parsear producto
        try:
            prod = parse_producto_local(user_message)
            
            if not prod["producto"]:
                return "No pude extraer el nombre del producto. Por favor indica así: 'Agregar [nombre], categoria [xxx], stock [xxx], min [xxx]'"
            
            added = add_product(prod)
            return f"Producto '{added.get('producto')}' agregado correctamente.\nCategoría: {added.get('categoria')}, Stock: {added.get('stock_actual')}, Mínimo: {added.get('stock_minimo')}"
        except Exception as e:
            return f"Error al agregar producto: {str(e)}. Por favor, intenta con: 'Agregar [nombre], categoria [cat], stock [num], min [num]'"

    inventory = read_inventory()

    INVENTORY_CONTEXT = f"""
    Inventario actual de la empresa (datos reales, no inventar).

    Usa estos datos únicamente como fuente de verdad.
    No los repitas en bruto, interprétalos como un asesor humano.

    Datos:
    {json.dumps(inventory, indent=2, ensure_ascii=False)}
    """

    client = _get_client()
    
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": INVENTORY_CONTEXT},
                    {"role": "user", "content": f"Solicitud del usuario: {user_message}"}
                ],
                temperature=0.6
            )

            message = response.choices[0].message.content
            if message and message.strip():
                return message.strip()

        except Exception:
            pass

        try:
            recovery_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": INVENTORY_CONTEXT},
                    {"role": "system", "content": RECOVERY_PROMPT},
                    {"role": "user", "content": f"Solicitud del usuario: {user_message}"}
                ],
                temperature=0.6
            )

            recovery_message = recovery_response.choices[0].message.content
            return recovery_message.strip() if recovery_message else (
                "Puedo ayudarte a revisar el estado de tu inventario. "
                "¿Qué te gustaría analizar?"
            )
        except Exception:
            pass
    
    # Fallback sin modelo: devolver resumen local del inventario
    low = low or user_message.lower()
    
    if "stock bajo" in low or "critico" in low:
        critical = [p for p in inventory.get("inventario", []) 
                   if p.get("stock_actual", 0) <= p.get("stock_minimo", 0)]
        if critical:
            return f"Productos en stock crítico: {', '.join([p['producto'] for p in critical])}"
        return "No hay productos en stock crítico."
    
    total = len(inventory.get("inventario", []))
    if total == 0:
        return "Tu inventario está vacío."
    
    return f"Tu inventario tiene {total} productos. ¿Quieres revisar stock bajo, movimientos sin registrar, o algo específico?"