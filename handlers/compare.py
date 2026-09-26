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


# ---------- EVENT NORMALIZER (FIXED) ----------
def normalize_event(event: str):
    if not event:
        return ""

    event = event.strip()

    # 🔥 FIX: normalize "None"
    if event.lower() in ["none", "null", ""]:
        return ""

    match = re.search(r"\[(.*?)\]", event)
    if match:
        return match.group(1).strip()

    return event


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
    context.user_data["count"] = 0

    msg = await query.edit_message_text(
        "📥 Send your list (paste or one by one)\n\n📊 Progress: 0 items\n\n[✅ Done]",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Done", callback_data="cmp_done")]
        ])
    )

    context.user_data["progress_msg_id"] = msg.message_id
    return WAITING_LIST


# ---------- COLLECT LIST ----------
async def collect_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    context.user_data["raw_list"].extend(lines)

    context.user_data["count"] = len(context.user_data["raw_list"])

    msg_id = context.user_data.get("progress_msg_id")

    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg_id,
                text=(
                    "📥 Send your list (paste or one by one)\n\n"
                    f"📊 Progress: {context.user_data['count']} items\n\n"
                    "[✅ Done]"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Done", callback_data="cmp_done")]
                ])
            )
        except:
            pass

    return WAITING_LIST


# ---------- DONE ----------
async def done_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text("⚙️ Comparing data...\n📊 Please wait...")

    return await process_list(update, context)


# ---------- PARSER ----------
def parse_user_line(line: str):
    try:
        if "➥" not in line:
            return None

        parts = line.split("|")

        rarity_emoji = parts[1].strip()
        name_part = parts[2].strip()

        name = name_part.split("[")[0].replace("x", "").strip()

        event = ""
        if "[" in name_part and "]" in name_part:
            event = normalize_event(name_part)

        return (
            name.lower().strip(),
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

    chat_id = update.effective_chat.id

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="⚙️ Comparing...\n📊 Building results..."
    )

    # ---------- USER SET (FIXED) ----------
    user_set = set()

    for line in raw_lines:
        parsed = parse_user_line(line)
        if parsed:
            name, event, _ = parsed

            key = (name.strip(), normalize_event(event))
            user_set.add(key)

    # ---------- DB ----------
    db_chars = list(characters.find({
        "anime": anime,
        "type": type_
    }))

    db_set = set()
    db_map = {}

    for c in db_chars:
        name = c["name"].strip().lower()
        event = normalize_event(str(c.get("event", "")))

        key = (name, event)

        db_set.add(key)
        db_map[key] = c

    # ---------- COMPARE ----------
    missing_from_user = db_set - user_set
    not_in_db = user_set - db_set

    # ---------- FORMAT ----------
    text = f"📊 *{anime.title()} ({'Waifu' if type_=='w' else 'Husbando'})*\n\n"

    text += "❌ *Missing Characters:*\n"
    id_list = []

    for key in sorted(missing_from_user):
        char = db_map[key]

        rarity_emoji = RARITY_EMOJI.get(char["rarity"], "⭐")
        event = normalize_event(str(char.get("event", "")))
        event_display = f"{event}" if event else ""

        text += f"{char['char_id']} : {char['name']} {event_display}\n"
        id_list.append(str(char["char_id"]))

    text += "\n⚠️ *Not in Bot Database:*\n"

    for key in sorted(not_in_db):
        name, event = key
        event_display = f"{event}" if event else ""
        text += f"{name} {event_display}\n"

    # ---------- IDS ----------
    ids = " ".join(sorted(set(id_list)))

    if ids:
        text += "\n📋 *Missing IDs (Global DB):*\n"
        text += f"`{ids}`"
    else:
        text += "\n📋 *Missing IDs:* None 🎉"

    # ---------- FINAL ----------
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=status_msg.message_id,
        text=text,
        parse_mode="Markdown"
    )

    return ConversationHandler.END


# ---------- HANDLER ----------
compare_handler = ConversationHandler(
    entry_points=[CommandHandler("compare", compare_start)],
    states={
        ASK_TYPE: [CallbackQueryHandler(select_type, pattern="^cmp_")],
        WAITING_LIST: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_list),
            CallbackQueryHandler(done_list, pattern="^cmp_done$")
        ],
    },
    fallbacks=[],
    per_chat=True,
    per_user=True,
    )
