from telegram import Update
from telegram.ext import ContextTypes
from db import characters, get_or_create_anime, normalize, is_admin
from parser import parse_caption


async def add_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    print("\n📩 ===== NEW MESSAGE =====")

    # 🚫 Safety checks
    if not message:
        print("❌ No message object")
        return

    if not message.photo:
        print("❌ Not a photo")
        return

    if not message.caption:
        print("❌ No caption")
        return

    user_id = message.from_user.id
    print("👤 User ID:", user_id)

    # 🔒 Admin check
    if not is_admin(user_id):
        print("🚫 Not an admin")
        await message.reply_text("❌ You are not allowed to add characters.")
        return

    print("✅ Admin verified")

    # 🧠 Parse caption
    data, error = parse_caption(message.caption)
    print("🧠 Parsed Data:", data)

    if error:
        print("❌ Parse Error:", error)
        await message.reply_text(f"❌ {error}")
        return

    # 🎬 Anime handling
    anime_id = get_or_create_anime(data["anime"])
    anime_key = normalize(data["anime"])

    print("🎬 Anime:", anime_key, "| ID:", anime_id)

    # ❌ Duplicate check
    existing = characters.find_one({
        "anime": anime_key,
        "char_id": data["char_id"]
    })

    if existing:
        print("⚠️ Duplicate found")
        await message.reply_text(
            f"❌ ID {data['char_id']} already exists in {data['anime']}"
        )
        return

    # 📸 File ID
    file_id = message.photo[-1].file_id
    print("🆔 File ID:", file_id)

    # 💾 Save to DB
    try:
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
            f"✅ Saved {data['name']} [{data['char_id']}]\n"
            f"📺 {data['anime']} | ⭐ {data['rarity']}"
        )

    except Exception as e:
        print("💥 DB ERROR:", str(e))
        await message.reply_text("❌ Failed to save to database.")
