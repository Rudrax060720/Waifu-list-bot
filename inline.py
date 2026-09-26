from telegram import InlineQueryResultCachedPhoto
from telegram.ext import ContextTypes
from db import characters
import uuid

# ---------- RARITY MAP ----------
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


# ---------- SEARCH ----------
def search_characters(query: str, offset: int, limit: int = 20):
    query = query.lower().strip()

    mongo_query = {}

    # 🎯 Event emoji search
    for emoji in EVENT_MAP.keys():
        if emoji in query:
            mongo_query = {"event": {"$regex": emoji}}
            break

    # 🎯 Rarity emoji search
    for emoji, rarity in RARITY_MAP.items():
        if emoji in query:
            mongo_query = {"rarity": rarity}
            break

    # 🎯 Normal text search
    if not mongo_query:
        mongo_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"anime": {"$regex": query, "$options": "i"}},
            ]
        }

    cursor = characters.find(mongo_query).skip(offset).limit(limit)

    return list(cursor)


# ---------- CAPTION ----------
def build_caption(char):
    rarity_emoji = RARITY_EMOJI.get(char["rarity"], "⭐")

    text = (
        f"OwO! Check out this {'waifu' if char['type']=='w' else 'husbando'}!\n\n"
        f"{char['display_anime']}\n"
        f"{char['char_id']}: {char['name']}"
    )

    # event
    if char.get("event"):
        emoji = char["event"].strip("[]")
        text += f" [{emoji}]"

    text += f"\n({rarity_emoji}𝙍𝘼𝙍𝙄𝙏𝙔:  {char['rarity'].title()})"

    # event name
    if char.get("event"):
        emoji = char["event"].strip("[]")
        event_name = EVENT_MAP.get(emoji, "")
        if event_name:
            text += f"\n\n{emoji} {event_name} {emoji}"

    return text


# ---------- INLINE HANDLER (REAL PAGINATION) ----------
async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    offset = int(update.inline_query.offset or 0)

    if not query:
        return

    LIMIT = 20

    results_db = search_characters(query, offset, LIMIT)

    results = []

    for char in results_db:
        results.append(
            InlineQueryResultCachedPhoto(
                id=str(uuid.uuid4()),  # unique ID
                photo_file_id=char["file_id"],
                caption=build_caption(char)
            )
        )

    # 🔥 NEXT OFFSET (pagination)
    next_offset = offset + LIMIT if len(results_db) == LIMIT else ""

    await update.inline_query.answer(
        results,
        cache_time=1,
        next_offset=str(next_offset)
    )
