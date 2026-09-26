import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    InlineQueryHandler
)

from config import BOT_TOKEN, OWNER_ID
from handlers.add_auto import add_character
from handlers.check import check_handler, pagination_handler
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

    threading.Thread(target=run_ping_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # ensure owner is admin
    add_admin(OWNER_ID)

    # 📸 FIXED HANDLER
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.CAPTION, add_character)
    )

    # 🔎 Check system
    app.add_handler(check_handler)
    app.add_handler(pagination_handler)

    # 👑 Admins
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CommandHandler("admins", list_admins))
    app.add_handler(CommandHandler("meadmin", check_admin))

    # 🔍 Inline
    app.add_handler(InlineQueryHandler(inline_query))

    print("✅ Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
