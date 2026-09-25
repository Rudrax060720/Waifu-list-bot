from telegram import Update
from telegram.ext import ContextTypes
from db import characters, get_or_create_anime, normalize, is_admin
from parser import parse_caption


async def add_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    print("📩 Incoming message")

    # 🚫 Ignore if no message (safety)
    if not message:
        return

    # 🚫 Ignore if not photo
    if not message.photo:
        print("❌ Not a photo")
        return

    # 🚫 Ignore if no caption
    if not message.caption:
        print("❌ No caption")
        return

    user_id = message.from_user.id
    print("👤 User ID:", user_id)

    # 🔒 DB-based admin check
    if not is_admin(user_id):
        print("🚫 Not an admin")
        return

    print("✅ Admin verified")

    # 🧠 Parse caption
    data, error = parse_caption(message.caption)

    if error:
        await message.reply_text(f"❌ {error}")
        return

    # 🎯 Get/Create anime
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
    print("🆔 File ID:", file_id)

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

    print("💾 Saved to DB")

    await message.reply_text(
        f"✅ Saved {data['name']} [{data['char_id']}] in {data['anime']}"
    )
