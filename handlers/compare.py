from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from db import characters, normalize
import re

ASK_TYPE, WAITING_LIST = range(2)


# ---------- RARITY ----------
RARITY_MAP = {
    "🔮": "limited",
    "🎐": "celestial",
    "💮": "exclusive",
    "🟡": "legendary",
    "🟠": "rare",
    "🔴": "medium",
    "🔵": "common",
}

RARITY_EMOJI = {v: k for k, v in RARITY_MAP.items()}


# ---------- EVENT NORMALIZER ----------
def normalize_event(event: str):
    if not event:
        return ""

    # extract emoji from [💞]
    match = re.search(r"\[(.*?)\]", event)
    if match:
        return match.group(1).strip()

    # already emoji
    return event.strip()


# ---------- START ----------
async def compare_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /compare <anime name>")
        return ConversationHandler.END

    anime = normalize(" ".join(context.args))

    context.user_data.clear()
    context.user_data["anime"] = anime

    keyboard = [[
        InlineKeyboardButton("👩 Waifu", callback_data="cmp_w"),
        InlineKeyboardButton("👨 Husbando", callback_data="cmp_h"),
    ]]

    await update.message.reply_text(
        f"📊 Compare for *{anime.title()}*\n\nSelect type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    return ASK_TYPE


# ---------- TYPE SELECT ----------
async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    type_ = query.data.split("_")[1]

    context.user_data["type"] = type_
    context.user_data["raw_list"] = []

    await query.edit_message_text(
        "📥 Send your list now.\n\nSend /endlist when done."
    )

    return WAITING_LIST


# ---------- COLLECT LIST ----------
async def collect_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith("/endlist"):
        return await process_list(update, context)

    context.user_data["raw_list"].append(text)
    return WAITING_LIST


# ---------- PARSER ----------
def parse_user_line(line: str):
    try:
        if "➥" not in line:
            return None

        parts = line.split("|")

        rarity_emoji = parts[1].strip()
        name_part = parts[2].strip()

        # extract name
        name = name_part.split("[")[0].strip()

        # extract event emoji
        event = ""
        if "[" in name_part and "]" in name_part:
            event = normalize_event(name_part)

        return (
            name.lower(),
            event,
            RARITY_MAP.get(rarity_emoji, "")
        )

    except:
        return None


# ---------- PROCESS ----------
async def process_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime = context.user_data["anime"]
    type_ = context.user_data["type"]
    raw_lines = context.user_data["raw_list"]

    # 🔹 USER SET
    user_set = set()

    for line in raw_lines:
        parsed = parse_user_line(line)
        if parsed:
            user_set.add(parsed)

    # 🔹 DB DATA
    db_chars = list(characters.find({
        "anime": anime,
        "type": type_
    }))

    db_set = set()
    db_map = {}

    for c in db_chars:
        event = normalize_event(str(c.get("event", "")))

        key = (
            c["name"].lower(),
            event,
            c["rarity"]
        )

        db_set.add(key)
        db_map[key] = c

    # ---------- COMPARE ----------
    missing_from_user = db_set - user_set
    not_in_db = user_set - db_set

    # ---------- FORMAT ----------
    text = f"📊 *{anime.title()} ({'Waifu' if type_=='w' else 'Husbando'})*\n\n"

    # ❌ Missing characters
    text += "❌ *Missing Characters:*\n"
    id_list = []

    for key in sorted(missing_from_user):
        char = db_map[key]

        rarity_emoji = RARITY_EMOJI.get(char["rarity"], "⭐")
        event = normalize_event(str(char.get("event", "")))

        event_display = f"[{event}]" if event else ""

        text += f"{rarity_emoji} {char['name']} {event_display}\n"
        id_list.append(str(char["char_id"]))

    # ⚠️ Not in DB
    text += "\n⚠️ *Not in Bot Database:*\n"

    for key in sorted(not_in_db):
        rarity_emoji = RARITY_EMOJI.get(key[2], "⭐")
        event_display = f"[{key[1]}]" if key[1] else ""

        text += f"{rarity_emoji} {key[0]} {event_display}\n"

    # 📋 Missing IDs
    text += "\n📋 *Missing IDs (Global DB):*\n"
    text += f"`{' '.join(sorted(set(id_list)))}`"

    await update.message.reply_text(text, parse_mode="Markdown")

    return ConversationHandler.END


# ---------- HANDLER ----------
compare_handler = ConversationHandler(
    entry_points=[CommandHandler("compare", compare_start)],
    states={
        ASK_TYPE: [CallbackQueryHandler(select_type, pattern="^cmp_")],
        WAITING_LIST: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_list)
        ],
    },
    fallbacks=[],
    per_chat=True,
    per_user=True,
  )
