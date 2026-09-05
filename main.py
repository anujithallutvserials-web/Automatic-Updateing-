import logging
import os
import re
import sqlite3
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)
from telegram.error import TelegramError

# ലോഗിങ് സെറ്റ് ചെയ്യുക
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ഫോർസ് സബ്സ്ക്രൈബ് ചെയ്യേണ്ട മെയിൻ ചാനലുകൾ
FORCE_SUB_CHANNELS = ["@Allutvserials", "@Anujith_Official1"]

# കോൺവെർസേഷൻ സ്റ്റേറ്റുകൾ
GET_DB_CHANNEL, GET_UPDATE_CHANNEL = range(2)

# --- SQLITE DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            user_id INTEGER PRIMARY KEY,
            db_channel INTEGER,
            update_channel TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_user_config(user_id, db_channel, update_channel):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configs (user_id, db_channel, update_channel)
        VALUES (?, ?, ?)
    ''', (user_id, db_channel, update_channel))
    conn.commit()
    conn.close()

def get_config_by_db(db_channel):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, update_channel FROM configs WHERE db_channel = ?', (db_channel,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None
# -----------------------------

# --- FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running successfully and Alive! 🚀"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# --------------------

async def check_subscriptions(bot, user_id):
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except TelegramError:
            return False
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    is_subbed = await check_subscriptions(context.bot, user_id)
    if not is_subbed:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/Allutvserials")],
            [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/Anujith_Official1")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "<b>⚠️ Access Denied!</b>\n\n"
            "You must join our channels first to use this bot. Please join both channels below and click 'Try Again'.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return

    if context.args:
        payload = context.args[0]
        if payload.startswith("getfile-"):
            await update.message.reply_text(f"📥 You requested file details: {payload}\n\nFile delivery processing...")
            return

    welcome_text = "Hi, I am an automatically update bot"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Setup My Channels", callback_data="setup_channels")],
        [InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id

    if query.data == "check_sub":
        is_subbed = await check_subscriptions(context.bot, user_id)
        if is_subbed:
            welcome_text = "Hi, I am an automatically update bot"
            keyboard = [
                [InlineKeyboardButton("⚙️ Setup My Channels", callback_data="setup_channels")],
                [InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(welcome_text, reply_markup=reply_markup)
        else:
            await query.answer("❌ Please join both channels first to proceed!", show_alert=True)

    elif query.data == "setup_channels":
        await query.message.reply_text(
            "⚙️ **Channel Setup Wizard**\n\n"
            "Please send your **Database Channel ID** (e.g., `-100xxxxxxxxxx`):\n"
            "*(Make sure this bot is added as an admin in your Database Channel)*"
        )
        return GET_DB_CHANNEL

    elif query.data == "help_menu":
        help_text = (
            "🤖 **Bot Help & Instructions Menu**\n\n"
            "ഈ ബോട്ട് എങ്ങനെ ഉപയോഗിക്കാം? (How to use):\n"
            "1️⃣ ബോട്ട് സ്റ്റാർട്ട് ചെയ്ത ശേഷം **'⚙️ Setup My Channels'** എന്ന ബട്ടൺ ക്ലിക്ക് ചെയ്യുക.\n"
            "2️⃣ ആദ്യം നിങ്ങളുടെ **Database Channel ID** അയക്കുക (നിങ്ങൾ ഫയലുകൾ അപ്‌ലോഡ് ചെയ്യുന്ന ചാനൽ).\n"
            "3️⃣ പിന്നീട് നിങ്ങളുടെ **Updates Channel ID** അല്ലെങ്കിൽ യൂസർനെയിം അയക്കുക (പോസ്റ്റുകൾ വരേേണ്ട ചാനൽ).\n\n"
            "⚠️ **மிக முக்கிய ശ്രദ്ധിക്കുക (Important Note):**\n"
            "നിങ്ങൾ നൽകുന്ന **ഡാറ്റാബേസ് ചാനലിലും (Database Channel)** അതുപോലെ **അപ്ഡേറ്റ്സ് ചാനലിലും (Updates Channel)** ഈ ബോട്ട് നിർബന്ധമായും **Administrator (അഡ്മിൻ)** ആയിരിക്കണം! എങ്കിൽ മാത്രമേ ബോട്ട് പ്രവർത്തനക്ഷമമാകൂ (Otherwise bot will be inactive).\n\n"
            "💬 **Contact Owner:**\n"
            "കൂടുതൽ സഹായത്തിന് ബന്ധപ്പെടുക: @Anujith1238"
        )
        
        keyboard = [
            [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")],
            [InlineKeyboardButton("« Back", callback_data="back_home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back_home":
        welcome_text = "Hi, I am an automatically update bot"
        keyboard = [
            [InlineKeyboardButton("⚙️ Setup My Channels", callback_data="setup_channels")],
            [InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(welcome_text, reply_markup=reply_markup)

async def get_db_channel_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db_chat_id = int(update.message.text.strip())
        context.user_data['temp_db_channel'] = db_chat_id
        
        await update.message.reply_text(
            "✅ Database Channel ID saved!\n\n"
            "Now, please send your **Updates Channel ID** or Username (e.g., `-100xxxxxxxxxx` or `@yourchannel`):\n"
            "*(Make sure this bot is added as an admin in your Updates Channel as well)*"
        )
        return GET_UPDATE_CHANNEL
    except ValueError:
        await update.message.reply_text("❌ Invalid ID! Please send a valid numeric Channel ID (Ex: -100123456789):")
        return GET_DB_CHANNEL

async def get_update_channel_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text_input = update.message.text.strip()
    
    try:
        if text_input.startswith("@"):
            update_chat_id = text_input
        else:
            update_chat_id = str(int(text_input))
            
        db_channel = context.user_data.get('temp_db_channel')
        
        save_user_config(user_id, db_channel, update_chat_id)
        
        await update.message.reply_text(
            "🎉 **Setup Successful!**\n\n"
            "Your Database Channel and Updates Channel have been successfully linked.\n"
            "Whenever you upload a video to your Database Channel, it will automatically post to your Updates Channel!"
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Error saving configuration: {e}\nPlease try again by clicking /start")
        return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Setup cancelled.")
    return ConversationHandler.END

async def auto_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post or update.message
    
    if not message:
        return

    incoming_chat_id = message.chat.id
    
    config = get_config_by_db(incoming_chat_id)
    if not config:
        return

    user_id, target_update_channel = config

    file_name = ""
    if message.document:
        file_name = message.document.file_name
    elif message.video:
        file_name = message.video.file_name or message.caption or "Unknown Video"
    elif message.caption:
        file_name = message.caption

    if not file_name:
        return

    clean_name = file_name.replace("_", " ").replace(".", " ")
    
    season_match = re.search(r's0?(\d+)', clean_name, re.IGNORECASE)
    season = season_match.group(1) if season_match else "01"
    
    ep_match = re.search(r'(?:ep?|episode)\s*(\d+)', clean_name, re.IGNORECASE)
    if ep_match:
        episode = ep_match.group(1)
    else:
        num_match = re.findall(r'\b(?:ep?|episode)?\s*(\d{1,4})\b', clean_name, re.IGNORECASE)
        episode = num_match[-1] if num_match else "01"

    quality_match = re.search(r'(480p|720p|1080p)', clean_name, re.IGNORECASE)
    quality = quality_match.group(1) if quality_match else "720p"

    title_clean = re.sub(
        r's0?\d+|ep?\s*\d+|episode|\b\d+\b|\b480p\b|\b720p\b|\b1080p\b|\bget\b|\breadypass\b|\bready\b|\bfor\b|\ba\b|\bnon\b|\bstop\b|\bmkv\b|\bmp4\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', 
        '', 
        clean_name, 
        flags=re.IGNORECASE
    )
    
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
    if not title_clean:
        title_clean = "Serial Video"

    caption_text = (
        f"<b>🍁𝑨𝒏𝒖j𝒊𝒕𝒉 𝑨𝒍𝒍𝒖 𝑻𝑽 𝑺𝒆𝒓𝒊𝒂ls🍁</b>\n"
        f"📁 <b>File Name :</b> {title_clean}\n"
        f"🎞 <b>Season :</b> {season.zfill(2)}\n"
        f"📌 <b>Episode :</b> {episode}\n"
        f"🎬 <b>Quality :</b> {quality}"
    )

    formatted_title_for_link = title_clean.replace(" ", "")
    file_unique_link = f"https://telegram.me/Anujith1bot?start=getfile-{formatted_title_for_link}-S{season.zfill(2)}E{episode}"
    
    keyboard = [
        [InlineKeyboardButton("📥 Get File", url=file_unique_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=int(target_update_channel) if target_update_channel.lstrip('-').isdigit() else target_update_channel,
            text=caption_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        logger.info(f"SQLite Dynamic auto post sent successfully to channel: {target_update_channel}!")
    except Exception as e:
        logger.error(f"Error sending dynamic auto post: {e}")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN is missing in Environment Variables!")
    
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()

    setup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^setup_channels$")],
        states={
            GET_DB_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_db_channel_step)],
            GET_UPDATE_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_update_channel_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)]
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(setup_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL | filters.TEXT), auto_post_handler))

    print("SQLite Multi-Tenant Bot with Help Instructions is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
                           
