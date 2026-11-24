import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN", "PASTE_TOKEN_HERE_ONLY_FOR_LOCAL_TEST")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Hello! I am a bot that deletes messages in groups and channels.\n\n"
        "1. Add me to your group/channel as admin (Delete messages permission ON).\n"
        "2. /delall - delete all messages\n"
        "3. /delfrom - reply to a message with this command to delete it and everything after it\n\n"
        "Co-Powerded by @SnowWorldz"
    )


async def is_admin(update: Update) -> bool:
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user is None or (msg.sender_chat and msg.sender_chat.id == chat.id):
        return True
    try:
        member = await chat.get_member(user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def delete_range(context, chat_id, start_id, end_id):
    deleted = 0
    first_error = ""
    ids = list(range(end_id, start_id - 1, -1))
    for i in range(0, len(ids), 100):
        batch = ids[i:i + 100]
        try:
            await context.bot.delete_messages(chat_id, batch)
            deleted += len(batch)
        except Exception as e:
            for mid in batch:
                try:
                    await context.bot.delete_message(chat_id, mid)
                    deleted += 1
                except Exception as e2:
                    if not first_error:
                        first_error = str(e2) or str(e)
        await asyncio.sleep(0.5)
    return deleted, first_error


async def report(context, chat_id, deleted, first_error):
    text = f"Done. Processed messages: {deleted}"
    if first_error:
        text += f"\nFirst error: {first_error}"
    try:
        await context.bot.send_message(chat_id, text)
    except Exception as e:
        print("Report error:", e)


async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    if chat.type == "private":
        await msg.reply_text("Please use this command in a group or channel where I am an admin.")
        return
    if not await is_admin(update):
        return
    deleted, err = await delete_range(context, chat.id, 1, msg.message_id)
    await report(context, chat.id, deleted, err)


async def delfrom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    if chat.type == "private":
        await msg.reply_text("Please use this command in a group or channel where I am an admin.")
        return
    if not await is_admin(update):
        return
    if not msg.reply_to_message:
        await context.bot.send_message(chat.id, "Reply to the message you want to start deleting from, then send /delfrom.")
        return
    deleted, err = await delete_range(context, chat.id, msg.reply_to_message.message_id, msg.message_id)
    await report(context, chat.id, deleted, err)


def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    kinds = filters.UpdateType.MESSAGE | filters.UpdateType.CHANNEL_POST
    app.add_handler(MessageHandler(filters.Regex(r"^/delall(@\w+)?$") & kinds, delall))
    app.add_handler(MessageHandler(filters.Regex(r"^/delfrom(@\w+)?$") & kinds, delfrom))
    app.run_polling(bootstrap_retries=-1)


if __name__ == "__main__":
    main()
