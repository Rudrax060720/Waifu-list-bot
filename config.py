# put your Telegram user IDs here
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "waifu_system")

# 👑 Keep ONLY owner (for security-critical commands)
OWNER_ID = int(os.getenv("OWNER_ID", "7562158122"))
