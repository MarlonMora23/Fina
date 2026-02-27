import sys
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.brain import decidir_intencion
from core.orchestrator import ejecutar_accion

TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes):
    await update.message.reply_text(
        "Hola, soy tu asesor financiero. ¿En qué puedo ayudarte hoy?"
    )


def _format_currency(value):
    try:
        n = int(value)
        return f"${n:,}"
    except:
        return f"${value}"


async def handle_message(update: Update, context: ContextTypes):
    texto = update.message.text or ""

    intent = decidir_intencion(texto)
    accion = ejecutar_accion(intent, texto)

    tipo = accion.get("type")

    if tipo == "registro":
        # El parserAgent ya registró y retorna un mensaje amigable
        msg = accion.get("message") or "✅ Movimiento registrado"
        await update.message.reply_text(msg)
        return

    if tipo == "resumen":
        # El financial_agent retorna análisis completo en "data"
        msg = accion.get("data") or accion.get("message") or "No tengo datos para analizar"
        await update.message.reply_text(msg)
        return

    if tipo == "inventario":
        msg = accion.get("message") or "No pude procesar tu solicitud"
        await update.message.reply_text(msg)
        return

    if tipo == "conversacion":
        msg = accion.get("message") or "No entiendo tu pregunta"
        await update.message.reply_text(msg)
        return
    
    # Fallback si no matchea nada
    await update.message.reply_text("No pude procesar tu solicitud. Intenta de nuevo.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == '__main__':
    main()