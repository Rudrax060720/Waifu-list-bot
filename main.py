import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    InlineQueryHandler,
    filters
)

from config import BOT_TOKEN, OWNER_ID
from db import add_admin

# handlers
from handlers.add_auto import add_character
from handlers.check import check_handler, pagination_handler
from handlers.admins import (
    add_admin_cmd,
    remove_admin_cmd,
    list_admins,
    check_admin
)
from handlers.inline import inline_query


# ---------- Ping Server (for Render) ----------
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


# ---------- Main Bot ----------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    # 🌐 Start ping server
    threading.Thread(target=run_ping_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # 🔐 Ensure OWNER is always admin
    add_admin(OWNER_ID)

    # ---------- Handlers ----------

    # 📸 Auto add (ONLY photo + caption)
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.Caption(True), add_character)
    )

    # 🔎 Check system
    app.add_handler(check_handler)
    app.add_handler(pagination_handler)

    # 👑 Admin commands
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CommandHandler("admins", list_admins))
    app.add_handler(CommandHandler("meadmin", check_admin))

    # 🔍 Inline search (keep LAST)
    app.add_handler(InlineQueryHandler(inline_query))

    print("✅ Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
