"""Bot de Telegram para consultar el inventario: python telegram_bot.py

Variables de entorno (ver .env.example):
    TELEGRAM_BOT_TOKEN  token del bot, creado con @BotFather
    ALLOWED_USER_IDS    IDs de Telegram autorizados, separados por comas
    INVENTORY_FILE      Excel con el inventario (por defecto, el de ejemplo)
"""

import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from inventory import answer, load_inventory

DEFAULT_INVENTORY = "inventory_example.xlsx"
WELCOME = "¡Hola! Soy tu bot de inventario. Escribe /buscar <objeto> o '¿Dónde está el martillo?'."


def parse_allowed_ids(raw):
    """'123, 456' -> {123, 456}"""
    try:
        return {int(part) for part in (raw or "").split(",") if part.strip()}
    except ValueError:
        raise SystemExit("ALLOWED_USER_IDS debe ser una lista de números separados por comas.")


def is_authorized(user_id, allowed):
    return user_id in allowed


def make_handlers(items, allowed):
    """Crea los manejadores; solo responden a los usuarios de `allowed`."""

    async def authorized(update):
        user = update.effective_user
        if user is None:
            return False
        if not is_authorized(user.id, allowed):
            await update.message.reply_text(
                f"No estás autorizado para usar este bot. Tu ID de Telegram es {user.id}."
            )
            return False
        return True

    async def start(update, context):
        if await authorized(update):
            await update.message.reply_text(WELCOME)

    async def search_command(update, context):
        if await authorized(update):
            await update.message.reply_text(answer(items, "buscar " + " ".join(context.args)))

    async def text_message(update, context):
        if await authorized(update):
            await update.message.reply_text(answer(items, update.message.text))

    return start, search_command, text_message


def build_application(token, items, allowed):
    start, search_command, text_message = make_handlers(items, allowed)
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buscar", search_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    return application


def main():
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN en el entorno o en .env (ver .env.example).")

    allowed = parse_allowed_ids(os.environ.get("ALLOWED_USER_IDS"))
    if not allowed:
        raise SystemExit(
            "Falta ALLOWED_USER_IDS: sin usuarios autorizados el bot no responde a nadie.\n"
            "Obtén tu ID de Telegram escribiendo a @userinfobot."
        )

    items = load_inventory(os.environ.get("INVENTORY_FILE", DEFAULT_INVENTORY))
    print(f"Inventario cargado: {len(items)} objetos. Bot en marcha (Ctrl+C para parar).")
    build_application(token, items, allowed).run_polling()


if __name__ == "__main__":
    main()
