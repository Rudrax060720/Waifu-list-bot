from telegram import Update
from telegram.ext import ContextTypes
from db import characters, get_or_create_anime, normalize
from parser import parse_caption

async def add_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    caption = update.message.caption
    if not caption:
        await update.message.reply_text("❌ Caption required")
        return

    data, error = parse_caption(caption)

    if error:
        await update.message.reply_text(f"❌ {error}")
        return

    # 🔥 Create / Get anime
    anime_id = get_or_create_anime(data["anime"])
    anime_key = normalize(data["anime"])

    # ❌ Duplicate character ID check (per anime)
    if characters.find_one({
        "anime": anime_key,
        "char_id": data["char_id"]
    }):
        await update.message.reply_text(
            f"❌ ID {data['char_id']} already exists in {data['anime']}"
        )
        return

    file_id = update.message.photo[-1].file_id

    # SAVE
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

    await update.message.reply_text(
        f"✅ Saved {data['name']} [{data['char_id']}] in {data['anime']} (Anime ID: {anime_id})"
    )
