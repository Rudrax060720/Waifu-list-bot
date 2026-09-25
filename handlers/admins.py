from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID
from db import add_admin, remove_admin, get_all_admins, is_admin


# ➕ Add Admin
async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # 🔒 Only OWNER can add admins
    if user.id != OWNER_ID:
        return

    # Method 1: Reply to a user
    if update.message.reply_to_message:
        new_admin_id = update.message.reply_to_message.from_user.id
    else:
        # Method 2: Use /addadmin <user_id>
        if not context.args:
            await update.message.reply_text("Usage:\n/addadmin <user_id> OR reply to a user")
            return

        try:
            new_admin_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return

    add_admin(new_admin_id)

    await update.message.reply_text(f"✅ Added admin: {new_admin_id}")


# ➖ Remove Admin
async def remove_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # 🔒 Only OWNER
    if user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/removeadmin <user_id>")
        return

    try:
        admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID")
        return

    remove_admin(admin_id)

    await update.message.reply_text(f"❌ Removed admin: {admin_id}")


# 📋 List Admins
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = get_all_admins()

    if not admins:
        await update.message.reply_text("⚠️ No admins set.")
        return

    text = "👑 Admins List:\n\n"

    for admin in admins:
        text += f"• {admin['user_id']}\n"

    await update.message.reply_text(text)


# 🔍 Check if YOU are admin
async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_admin(user_id):
        await update.message.reply_text("✅ You are an admin")
    else:
        await update.message.reply_text("❌ You are NOT an admin")
