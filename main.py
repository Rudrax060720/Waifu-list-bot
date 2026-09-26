import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    InlineQueryHandler
)

from config import BOT_TOKEN, OWNER_ID
from handlers.add_auto import add_character
from handlers.check import check_handler, pagination_handler
from handlers.compare import compare_handler
from handlers.admins import (
    add_admin_cmd,
    remove_admin_cmd,
    list_admins,
    check_admin
)
from handlers.inline import inline_query
from db import add_admin


# ---------- Ping Server ----------
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return


def run_ping_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    print(f"🌐 Ping server running on port {port}")
    server.serve_forever()


# ---------- MAIN ----------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    # 🌐 Keepalive server (Render)
    threading.Thread(target=run_ping_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # 🔐 ensure owner is admin
    add_admin(OWNER_ID)

    # ==============================
    # 🔥 HANDLER ORDER (OPTIMIZED)
    # ==============================

    # 1️⃣ Conversation handlers (highest priority)
    app.add_handler(compare_handler)
    app.add_handler(check_handler)

    # 2️⃣ Callback handlers (IMPORTANT for Done button + pagination)
    app.add_handler(pagination_handler)

    # 3️⃣ Admin commands
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CommandHandler("admins", list_admins))
    app.add_handler(CommandHandler("meadmin", check_admin))

    # 4️⃣ Inline mode
    app.add_handler(InlineQueryHandler(inline_query))

    # 5️⃣ Media handler LAST (important)
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.CAPTION, add_character)
    )

    print("✅ Bot running...")

    # 🚀 Safe polling
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
