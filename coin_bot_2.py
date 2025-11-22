from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import datetime
import asyncio

BOT_TOKEN = "8211259694:AAGuKDhZYt20ZDM67SJBFvnCB-jV9_sjg8s"
MY_CHAT_ID = 7736278920

SUPPORT_USERNAME = "@rafi_admin_01"
INSTAGRAM_USERNAME = "@akashmolla207"

COINS_PER_UNIT = 1000
TK_PER_UNIT = 6

user_steps = {}
user_history = {}

menu_buttons = ReplyKeyboardMarkup(
    [["💰 Coin Transfer", "📞 Support"]],
    resize_keyboard=True,
    one_time_keyboard=False
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Choose an option from the menu below 👇",
        reply_markup=menu_buttons
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # ----- Menu buttons -----
    if text == "📞 Support":
        await update.message.reply_text(
            f"📞 Support Contact:\nTelegram: {SUPPORT_USERNAME}",
            reply_markup=menu_buttons
        )
        return

    if text == "💰 Coin Transfer":
        user_steps[user_id] = "ask_username"
        await update.message.reply_text(
            f"💰 Coin Transfer\n\nMy Instagram: {INSTAGRAM_USERNAME}\n\n"
            f"Step 1: Reply with your username from where you sent the coin.",
            reply_markup=menu_buttons
        )
        return

    # ----- Step-by-step Coin Transfer -----
    if user_id in user_steps:
        step = user_steps[user_id]

        if step == "ask_username":
            context.user_data["coin_username"] = text
            user_steps[user_id] = "ask_amount"
            await update.message.reply_text(
                f"✔ Username received: {text}\nStep 2: Reply with how many coins you transferred.",
                reply_markup=menu_buttons
            )

        elif step == "ask_amount":
            if not text.isdigit():
                await update.message.reply_text(
                    "❌ Please enter a valid number for coins.",
                    reply_markup=menu_buttons
                )
                return

            context.user_data["coin_amount"] = int(text)
            user_steps[user_id] = "confirm_transfer"

            username = context.user_data["coin_username"]
            amount = context.user_data["coin_amount"]

            # Inline confirm button
            keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_transfer")]]
            await update.message.reply_text(
                f"💰 Please confirm your Coin Transfer:\n\n"
                f"👤 Username: {username}\n"
                f"💰 Amount: {amount} coins",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "confirm_transfer":
        username = context.user_data.get("coin_username")
        amount = context.user_data.get("coin_amount")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate total Tk
        total_tk = (amount / COINS_PER_UNIT) * TK_PER_UNIT

        # Save history
        user_history.setdefault(user_id, []).append({
            "username": username,
            "amount": amount,
            "total_tk": total_tk,
            "time": now
        })

        # Notify admin
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=(
                f"📩 New Coin Transfer Request\n"
                f"User ID: {user_id}\nUsername: {username}\nCoins: {amount}\n"
                f"Total Tk: {total_tk}\nTime: {now}"
            )
        )

        # Clear step
        if user_id in user_steps: del user_steps[user_id]
        context.user_data.clear()

        # Success message
        await query.edit_message_text(
            f"✅ Coin Transfer Successful!\n"
            f"Username: {username}\n"
            f"Coins: {amount}\n"
            f"Total: {total_tk} tk\n"
            f"Thank you!",
            reply_markup=None
        )


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id == MY_CHAT_ID:
        if not user_history:
            await update.message.reply_text("No coin transfers yet.")
            return
        text = "📊 All Users Coin Transfer History:\n\n"
        for uid, records in user_history.items():
            for rec in records:
                text += (f"User ID: {uid}\nUsername: {rec['username']}\nCoins: {rec['amount']}"
                         f"\nTotal Tk: {rec['total_tk']}\nTime: {rec['time']}\n\n")
        await update.message.reply_text(text)
    else:
        records = user_history.get(user_id, [])
        if not records:
            await update.message.reply_text("You have no coin transfer history yet.")
            return
        text = "📊 Your Coin Transfer History:\n\n"
        for rec in records:
            text += (f"Username: {rec['username']}\nCoins: {rec['amount']}"
                     f"\nTotal Tk: {rec['total_tk']}\nTime: {rec['time']}\n\n")
        await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Menu\n/history - View your history\n/help - Help Menu"
    )


async def keep_alive():
    # Simple keep-alive loop to prevent bot from sleeping in Android hosting apps
    while True:
        await asyncio.sleep(60)  # ping every 60 seconds


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Run keep_alive loop in background
    app.job_queue.run_repeating(lambda ctx: None, interval=60, first=0)

    print("Bot running (Hosting-ready for Play Store Telegram hosting apps)…")
    app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())