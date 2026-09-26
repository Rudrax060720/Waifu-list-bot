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
PAGE_SIZE = 10


# ---------- RARITY MAP ----------
RARITY_EMOJI = {
    "limited": "🔮",
    "celestial": "🎐",
    "exclusive": "💮",
    "legendary": "🟡",
    "rare": "🟠",
    "medium": "🔴",
    "common": "🔵",
}


# ---------- EVENT MAP ----------
EVENT_MAP = {
    "👶": "Chibi",
    "👥": "Duo",
    "🎮": "Game",
    "🤝🏻": "Group",
    "📙": "Manga",
    "⛰": "Adventurer",
    "🏀": "Basketball",
    "🐰": "Bunny",
    "🐎": "Cowboy",
    "🎄": "Christmas",
    "🎃": "Halloween",
    "👘": "Kimono",
    "🧹": "Maid",
    "🎸": "Musician",
    "🚓": "Officer",
    "🎒": "School",
    "🏖": "Summer",
    "☃️": "Winter",
    "🎩": "Tuxedo",
    "🏴‍☠️": "Pirate",
    "🏁": "Racer",
    "🩺": "Doctor",
    "⚽": "Soccer",
    "💞": "Valentine",
    "🪐": "Cosmonaut",
    "🀄️": "Abbess",
    "💍": "Bride",
    "🎊": "Cheerleaders",
    "🥻": "Saree",
    "🎾": "Tennis",
}


# ---------- START ----------
async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📺 Enter anime name:")
    return ASK_ANIME


# ---------- GET ANIME ----------
async def get_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_input = update.message.text.strip()
    context.user_data["anime"] = normalize(anime_input)

    keyboard = [[
        InlineKeyboardButton("👩 Waifu", callback_data="type_w"),
        InlineKeyboardButton("👨 Husbando", callback_data="type_h"),
    ]]

    await update.message.reply_text(
        "Select type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ASK_TYPE


# ---------- FORMAT CHARACTER ----------
def format_character(char):
    rarity_emoji = RARITY_EMOJI.get(char["rarity"], "⭐")

    event_display = ""
    if char.get("event"):
        emoji = char["event"].strip("[]")
        event_name = EVENT_MAP.get(emoji, "")
        if event_name:
            event_display = f" [{emoji} {event_name}]"
        else:
            event_display = f" [{emoji}]"

    return f"{rarity_emoji} {char['char_id']}: {char['name']}{event_display}"


# ---------- SHOW PAGE ----------
async def show_page(query, context, page: int):
    anime = context.user_data.get("anime")
    type_ = context.user_data.get("type")

    results = get_characters_by_anime_and_type(anime, type_)

    if not results:
        await query.edit_message_text("❌ No characters found.")
        return

    total = len(results)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = results[start:end]

    text = f"📚 {anime.title()} ({'Waifu' if type_=='w' else 'Husbando'})\n"
    text += f"📄 Page {page+1} / {(total-1)//PAGE_SIZE + 1}\n\n"

    for char in page_data:
        text += format_character(char) + "\n"

    # ---------- BUTTONS ----------
    buttons = []

    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}"))

    if end < total:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))

    keyboard = [buttons] if buttons else []

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )


# ---------- TYPE SELECT ----------
async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["type"] = query.data.split("_")[1]

    await show_page(query, context, 0)
    return ConversationHandler.END


# ---------- PAGINATION ----------
async def pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[1])
    await show_page(query, context, page)


# ---------- HANDLER ----------
check_handler = ConversationHandler(
    entry_points=[CommandHandler("check", check_start)],
    states={
        ASK_ANIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime)],
        ASK_TYPE: [CallbackQueryHandler(get_type, pattern="^type_")],
    },
    fallbacks=[]
)

pagination_handler = CallbackQueryHandler(pagination, pattern="^page_")
