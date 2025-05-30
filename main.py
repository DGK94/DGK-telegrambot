import os
import logging
import asyncio
import requests
from telegram import Update, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv "7637420996:AAFFFOTd99wjOwaOX0L6JXvaRjG_C2jmWwQ"
ADMIN_USERNAME = "DGKon"  # your telegram username (without @)

# Example signals (You can update later or fetch dynamically)
signals = [
    {
        "pair": "BTCUSDT",
        "entry": 27300,
        "sl": 27000,
        "tp1": 27500,
        "tp2": 28000,
        "posted": False,
        "status": "open",
    },
    {
        "pair": "ETHUSDT",
        "entry": 1850,
        "sl": 1800,
        "tp1": 1900,
        "tp2": 1950,
        "posted": False,
        "status": "open",
    },
]

past_signals = []

def is_admin(update: Update):
    user = update.effective_user
    return user and user.username == ADMIN_USERNAME

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update):
        await update.message.reply_text(f"Welcome {update.effective_user.first_name}! ✅ You are the admin.")
    else:
        await update.message.reply_text("❌ You are not authorized to use this bot.")

def fetch_price(pair: str) -> float:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return -1

def format_signal_message(signal):
    return (
        f"🚀 *Crypto Signal Alert* 🚀\n\n"
        f"*Pair:* {signal['pair']}\n"
        f"*Entry:* {signal['entry']}\n"
        f"*Stop Loss:* {signal['sl']}\n"
        f"*Take Profit 1:* {signal['tp1']}\n"
        f"*Take Profit 2:* {signal['tp2']}\n\n"
        f"⚠️ *Not financial advice*"
    )

def format_performance_summary():
    if not past_signals:
        return "📊 No previous signals.\n\n"
    summary = "📊 *Last Signal Results:*\n\n"
    for idx, sig in enumerate(past_signals[-5:], 1):
        emoji = "✅" if sig['status'] == "tp_hit" else "❌"
        summary += f"{idx}) {sig['pair']} | Entry: {sig['entry']} | {emoji}\n"
    return summary + "\n---\n\n"

async def post_signals_periodically(context: ContextTypes.DEFAULT_TYPE):
    for signal in signals:
        if not signal["posted"]:
            msg = format_performance_summary() + format_signal_message(signal)
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN
            )
            signal["posted"] = True
            break

    for signal in signals:
        if signal["posted"] and signal["status"] == "open":
            price = fetch_price(signal["pair"])
            if price == -1:
                continue
            if price >= signal["tp1"]:
                signal["status"] = "tp_hit"
                past_signals.append(signal.copy())
                logger.info(f"TP hit for {signal['pair']}")
            elif price <= signal["sl"]:
                signal["status"] = "sl_hit"
                past_signals.append(signal.copy())
                logger.info(f"SL hit for {signal['pair']}")

async def start_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Unauthorized.")
        return
    chat_id = update.effective_chat.id
    await context.job_queue.run_repeating(post_signals_periodically, interval=240, first=3, chat_id=chat_id)
    await update.message.reply_text("✅ Signal posting started.")

async def stop_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Unauthorized.")
        return
    context.job_queue.stop()
    await update.message.reply_text("🛑 Signal posting stopped.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start bot\n"
        "/help - Commands\n"
        "/startsignals - Start auto-posting\n"
        "/stopsignals - Stop posting"
    )

def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("startsignals", start_job))
    app_bot.add_handler(CommandHandler("stopsignals", stop_job))
    print("Bot started...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
  
