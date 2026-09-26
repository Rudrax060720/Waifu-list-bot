from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters
)
from db import get_characters_by_anime_and_type, normalize

ASK_ANIME, ASK_TYPE = range(2)


# ---------- START ----------
async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📺 Enter anime name:")
    return ASK_ANIME


# ---------- GET ANIME ----------
async def get_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_input = update.message.text.strip()
    context.user_data["anime"] = normalize(anime_input)

    keyboard = [[
        InlineKeyboardButton("👩 Waifu", callback_data="w"),
        InlineKeyboardButton("👨 Husbando", callback_data="h"),
    ]]

    await update.message.reply_text(
        "Select type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ASK_TYPE


# ---------- GET TYPE ----------
async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    type_ = query.data
    anime = context.user_data.get("anime")

    results = get_characters_by_anime_and_type(anime, type_)

    if not results:
        await query.edit_message_text("❌ No characters found.")
        return ConversationHandler.END

    text = f"📚 {anime.title()}:\n\n"

    for char in results[:20]:
        text += f"• {char['char_id']}: {char['name']} ({char['rarity']})\n"

    if len(results) > 20:
        text += f"\n...and {len(results) - 20} more"

    await query.edit_message_text(text)

    return ConversationHandler.END


# ---------- HANDLER ----------
check_handler = ConversationHandler(
    entry_points=[CommandHandler("check", check_start)],
    states={
        ASK_ANIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime)],
        ASK_TYPE: [CallbackQueryHandler(get_type)],
    },
    fallbacks=[]
)
