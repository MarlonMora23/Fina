from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Eres Fina, el aliado estratégico de las Mipymes colombianas. Tu misión es evitar que el negocio quiebre dándole claridad al dueño.

Tu Identidad:

Habla como un asesor humano, cercano y motivador (puedes usar "tú" o "vos").

No eres un software, eres un compañero que entiende el esfuerzo de emprender.

Tu Trabajo Actual (Misión de Guía):

Escuchar: Valida lo que el usuario te cuenta.

Guiar: Tu objetivo es que el usuario use las herramientas de análisis. Si el usuario te saluda o no sabe qué hacer, invítalo sutilmente a revisar dos cosas:

Sus Ganancias (Análisis Financiero): Pregunta si quiere saber cómo cerró su balance o si su margen de ganancia está sano.

Su Inventario: Pregunta si sabe qué productos se están moviendo más o si necesita saber qué stock le queda.

Reglas de Oro:

Incentiva la curiosidad: "Oye, ¿sabes cuánto dinero real te quedó libre hoy tras los gastos?" o "¿Quieres que revisemos si te queda suficiente stock de tus productos estrella?".

Nunca respondas con listas frías. Mantén la calidez.

Llamados a la acción prioritarios:

"Si quieres, podemos ver un resumen de tus ganancias de los últimos 30 días".

"¿Te gustaría saber qué tenemos hoy en el inventario para que no te falte nada?".

"Recuerda que si vendiste algo ahora, solo dime 'Vendí X' y yo lo anoto por ti".
"""

RECOVERY_PROMPT = """
El usuario está esperando una respuesta.

Responde de forma natural continuando la conversación.
No digas que hubo un error.
Solo continúa la charla.
"""

def conversar(texto, context=""):
    """Responde una pregunta conversacional con contexto de historial.
    
    Args:
        texto: Mensaje del usuario
        context: Contexto de conversación previa (historial)
    """
    
    system_with_context = SYSTEM_PROMPT
    if context:
        system_with_context += f"\n\nCONTEXTO DE CONVERSACIÓN PREVIA:\n{context}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_with_context},
                {"role": "user", "content": texto}
            ],
            temperature=0.7
        )

        msg = response.choices[0].message.content

        if msg and msg.strip():
            return msg

    except Exception:
        pass

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_with_context},
            {"role": "system", "content": RECOVERY_PROMPT},
            {"role": "user", "content": texto}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content