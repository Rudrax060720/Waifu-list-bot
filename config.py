# put your Telegram user IDs here
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "waifu_system")

# Convert ENV string → list of ints
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
