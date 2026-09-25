from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN
from handlers.add_auto import add_character

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Only process photos WITH captions (important)
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.Caption(True), add_character)
    )

    print("✅ Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
