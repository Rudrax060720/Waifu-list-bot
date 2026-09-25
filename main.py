from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN
from handler import add_character

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.PHOTO, add_character))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
