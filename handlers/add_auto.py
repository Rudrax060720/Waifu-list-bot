from telegram import Update
from telegram.ext import ContextTypes
from config import ADMINS
from db import characters, get_or_create_anime, normalize
from parser import parse_caption

async def add_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # 🚫 Ignore if not photo
    if not message.photo:
        return

    # 🚫 Ignore if no caption
    if not message.caption:
        return

    # 🔒 ADMIN LIST CHECK
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return  # ❌ completely ignore

    # 🧠 Parse caption
    data, error = parse_caption(message.caption)

    if error:
        await message.reply_text(f"❌ {error}")
        return

    # 🎯 Get/Create anime (auto anime ID)
    anime_id = get_or_create_anime(data["anime"])
    anime_key = normalize(data["anime"])

    # ❌ Duplicate character ID check
    if characters.find_one({
        "anime": anime_key,
        "char_id": data["char_id"]
    }):
        await message.reply_text(
            f"❌ ID {data['char_id']} already exists in {data['anime']}"
        )
        return

    file_id = message.photo[-1].file_id

    # 💾 Save to DB
    characters.insert_one({
        "anime_id": anime_id,
        "anime": anime_key,
        "display_anime": data["anime"],
        "char_id": data["char_id"],
        "name": data["name"],
        "rarity": data["rarity"],
        "event": data["event"],
        "event_name": data["event_name"],
        "type": data["type"],
        "file_id": file_id
    })

    await message.reply_text(
        f"✅ Saved {data['name']} [{data['char_id']}] in {data['anime']}"
    )
