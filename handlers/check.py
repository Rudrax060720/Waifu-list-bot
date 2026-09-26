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
    "👶": "𝑪𝒉𝒊𝒃𝒊",
    "👥": "𝑫𝒖𝒐",
    "🎮": "𝑮𝒂𝒎𝒆",
    "🤝🏻": "𝑮𝒓𝒐𝒖𝒑",
    "📙": "𝑴𝒂𝒏𝒈𝒂",
    "⛰": "𝑨𝒅𝒗𝒆𝒏𝒕𝒖𝒓𝒆𝒓",
    "🏀": "𝑩𝒂𝒔𝒌𝒆𝒕𝒃𝒂𝒍𝒍",
    "🐰": "𝑩𝒖𝒏𝒏𝒚",
    "🐎": "𝑪𝒐𝒘𝒃𝒐𝒚",
    "🎄": "𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔",
    "🎃": "𝑯𝒂𝒍𝒍𝒐𝒘𝒆𝒆𝒏",
    "👘": "𝑲𝒊𝒎𝒐𝒏𝒐",
    "🧹": "𝑴𝒂𝒊𝒅",
    "🎸": "𝑴𝒖𝒔𝒊𝒄𝒊𝒂𝒏",
    "🚓": "𝑶𝒇𝒇𝒊𝒄𝒆𝒓",
    "🎒": "𝑺𝒄𝒉𝒐𝒐𝒍",
    "🏖": "𝑺𝒖𝒎𝒎𝒆𝒓",
    "☃️": "𝑾𝒊𝒏𝒕𝒆𝒓",
    "🎩": "𝑻𝒖𝒙𝒆𝒅𝒐",
    "🏴‍☠️": "𝑷𝒊𝒓𝒂𝒕𝒆",
    "🏁": "𝑹𝒂𝒄𝒆𝒓",
    "🩺": "𝑫𝒐𝒄𝒕𝒐𝒓",
    "⚽": "𝑺𝒐𝒄𝒄𝒆𝒓",
    "💞": "𝑽𝒂𝒍𝒆𝒏𝒕𝒊𝒏𝒆",
    "🪐": "𝑪𝒐𝒔𝒎𝒐𝒏𝒂𝒖𝒕",
    "🀄️": "𝑨𝒃𝒃𝒆𝒔𝒔",
    "💍": "𝑩𝒓𝒊𝒅𝒆",
    "🎊": "𝑪𝒉𝒆𝒆𝒓𝒍𝒆𝒂𝒅𝒆𝒓𝒔",
    "🥻": "𝑺𝒂𝒓𝒆𝒆",
    "🎾": "𝑻𝒆𝒏𝒏𝒊𝒔",
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
        rarity_emoji = RARITY_EMOJI.get(char["rarity"], "⭐")

        event_display = ""
        if char.get("event"):
            emoji = char["event"].strip("[]")
            event_display = f" [{emoji}]"

        text += f"{rarity_emoji} {char['char_id']}: {char['name']}{event_display}\n"

    # ---------- Buttons ----------
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

    type_ = query.data.split("_")[1]
    context.user_data["type"] = type_

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
    fallbacks=[],
    per_message=True  # ✅ FIXED WARNING
)

pagination_handler = CallbackQueryHandler(pagination, pattern="^page_")
