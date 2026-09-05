import logging
import os
import re
import sqlite3
from urllib.parse import quote
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

# ലോഗിങ് സെറ്റ് ചെയ്യുക
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# കോൺവെർസേഷൻ സ്റ്റേറ്റുകൾ (Setup States)
GET_UPDATE_CHANNEL, GET_DB_CHANNEL, GET_TARGET_LINK, GET_FILE_FORMAT, GET_TOP_HEADING = range(5)

# --- SQLITE DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            user_id INTEGER PRIMARY KEY,
            update_channel TEXT,
            db_channel INTEGER,
            target_link TEXT,
            file_format TEXT,
            top_heading TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_user_config(user_id, update_channel, db_channel, target_link, file_format, top_heading):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configs (user_id, update_channel, db_channel, target_link, file_format, top_heading)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, update_channel, db_channel, target_link, file_format, top_heading))
    conn.commit()
    conn.close()

def get_config_by_db(db_channel):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, update_channel, target_link, file_format, top_heading FROM configs WHERE db_channel = ?', (db_channel,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1], row[2], row[3], row[4]
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        payload = context.args[0]
        if payload.startswith("getfile-"):
            await update.message.reply_text(f"📥 You requested file details: {payload}\n\nFile delivery processing...")
            return

    welcome_text = "Hi, I am an automatically update bot"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Setup My Channels", callback_data="setup_channels")],
        [InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")],
        [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# /admins കമാൻഡ് ഹാൻഡ്‌ലർ
async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_text = (
        "👑 **Admin Information**\n\n"
        "If you need any support or want to contact the admin, please reach out to:\n"
        "💬 **Contact:** @Anujith1238"
    )
    keyboard = [[InlineKeyboardButton("👤 Chat with Admin", url="https://t.me/Anujith1238")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "setup_channels":
        await query.message.edit_text(
            "⚙️ **Channel Setup Wizard**\n\n"
            "1️⃣ Please send your **Updates Channel ID** or Username (e.g., `-100xxxxxxxxxx` or `@yourchannel`):\n"
            "⚠️ *(Make sure this bot is added as an **Administrator** in this Updates Channel)*"
        )
        return GET_UPDATE_CHANNEL

    elif query.data == "help_menu":
        help_text = (
            "🤖 **Bot Help & Instructions Menu**\n\n"
            "How to use this bot:\n"
            "1️⃣ First, send your **Updates Channel ID** or Username (Where posts should arrive, and the bot **MUST be an Administrator**).\n"
            "2️⃣ Second, send your **Database Channel ID** (Where you upload your files, and the bot **MUST be an Administrator**).\n"
            "3️⃣ Third, send your **URL link, Channel/Group ID, or Bot Username** (for the Get File button target).\n"
            "4️⃣ Fourth, select your preferred **File Format** (Text or Video format).\n"
            "5️⃣ Finally, send your custom **Top Heading** text (Which will appear at the top of every post).\n\n"
            "⚠️ **Important Note:**\n"
            "This bot must be an **Administrator** in both channels! Otherwise, the bot will not work.\n\n"
            "💬 **Contact Owner:**\n"
            "For additional support, contact: @Anujith1238"
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
            [InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")],
            [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(welcome_text, reply_markup=reply_markup)

async def get_update_channel_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    try:
        if text_input.startswith("@") or text_input.startswith("https://"):
            update_chat_id = text_input
        else:
            update_chat_id = str(int(text_input))
            
        context.user_data['temp_update_channel'] = update_chat_id
        
        await update.message.reply_text(
            "✅ Updates Channel saved successfully!\n\n"
            "2️⃣ Now, please send your **Database Channel ID** (e.g., `-100xxxxxxxxxx`):\n"
            "⚠️ *(Make sure this bot is added as an **Administrator** in your Database Channel)*"
        )
        return GET_DB_CHANNEL
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid format: {e}\nPlease send a valid Channel ID or Username:")
        return GET_UPDATE_CHANNEL

async def get_db_channel_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db_chat_id = int(update.message.text.strip())
        context.user_data['temp_db_channel'] = db_chat_id
        
        await update.message.reply_text(
            "✅ Database Channel ID saved successfully!\n\n"
            "3️⃣ Now, please send your **URL link, Channel/Group ID, or Bot Username** (for the Get File button target):"
        )
        return GET_TARGET_LINK
    except ValueError:
        await update.message.reply_text("❌ Invalid ID! Please send a valid numeric Database Channel ID (Ex: -100123456789):")
        return GET_DB_CHANNEL

async def get_target_link_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_link_input = update.message.text.strip()
    context.user_data['temp_target_link'] = target_link_input

    keyboard = [
        [InlineKeyboardButton("📄 Text Format", callback_data="fmt_text")],
        [InlineKeyboardButton("🎬 Video Format", callback_data="fmt_video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Target Link/ID saved successfully!\n\n"
        "4️⃣ Please select your preferred **File Format** (Text or Video):",
        reply_markup=reply_markup
    )
    return GET_FILE_FORMAT

async def get_file_format_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['temp_file_format'] = "Text" if query.data == "fmt_text" else "Video"

    await query.message.edit_text(
        "✅ File Format saved successfully!\n\n"
        "5️⃣ Finally, please type and send your custom **Top Heading** text (e.g., `🍁Anujith Allu TV Serials🍁`):"
    )
    return GET_TOP_HEADING

async def get_top_heading_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    top_heading = update.message.text.strip()

    update_channel = context.user_data.get('temp_update_channel')
    db_channel = context.user_data.get('temp_db_channel')
    target_link = context.user_data.get('temp_target_link')
    file_format = context.user_data.get('temp_file_format')

    save_user_config(user_id, update_channel, db_channel, target_link, file_format, top_heading)

    success_msg = (
        "🎉 **Setup Successful!**\n\n"
        "Your configurations have been saved successfully:\n"
        f"📢 **Updates Channel:** `{update_channel}`\n"
        f"📁 **Database Channel:** `{db_channel}`\n"
        f"🔗 **Target Link/ID:** `{target_link}`\n"
        f"⚙️ **File Format:** `{file_format}`\n"
        f"🏷 **Top Heading:** {top_heading}\n\n"
        "Your bot is now fully configured and ready to work!"
    )

    keyboard = [
        [InlineKeyboardButton("⚙️ Setup Again", callback_data="setup_channels")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(success_msg, reply_markup=reply_markup, parse_mode="HTML")
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

    user_id, target_update_channel, target_link, file_format, top_heading = config

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

    quality_match = re.search(r'(480p|576p|720p|1080p)', clean_name, re.IGNORECASE)
    quality = quality_match.group(1) if quality_match else "720p"

    # ഫയൽ പേര് ക്ലീൻ ചെയ്ത് തീയതികളും മാസങ്ങളും അധിക വാക്കുകളും ഒഴിവാക്കി കൃത്യമായ സീരിയൽ പേര് (ഉദാ: Karnan) മാത്രം എടുക്കൽ
    title_part_match = re.split(r'(?:s0?\d+|ep?\s*\d+|episode|\b480p\b|\b576p\b|\b720p\b|\b1080p\b|\bweb\b|\b2020\b|\b2021\b|\b2022\b|\b2023\b|\b2024\b|\b2025\b|\b2026\b)', clean_name, flags=re.IGNORECASE)
    base_title = title_part_match[0].strip() if title_part_match else clean_name

    unwanted_words = [
        'ramesh', 'helps', 'nidhi', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 
        'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'snxt', 'web', 'dl', 'tamil', 
        'malayalam', 'aac2', 'aac', 'h', '2020', '2021', '2022', '2023', '2024', '2025', '2026'
    ]
    words = base_title.split()
    filtered_words = [w for w in words if w.lower() not in unwanted_words]
    
    if filtered_words:
        title_clean = filtered_words[0]
    else:
        title_clean = "Serial Video"

    heading_to_show = top_heading if top_heading else "🍁Anujith Allu TV Serials🍁"

    caption_text = (
        f"<b>{heading_to_show}</b>\n"
        f"📁 <b>File Name :</b> {file_name}\n"
        f"🎞 <b>Season :</b> {season.zfill(2)}\n"
        f"📌 <b>Episode :</b> {episode}\n"
        f"🎬 <b>Quality :</b> {quality}\n"
        f"📌 <b>Format :</b> {file_format}"
    )

    encoded_title = quote(title_clean)
    file_unique_link = f"https://telegram.me/Anujith1bot?start=getfile-{encoded_title}-S{season.zfill(2)}E{episode}"
    
    if target_link and target_link.startswith("https://"):
        keyboard = [
            [InlineKeyboardButton("🔗 Visit Link", url=target_link)],
            [InlineKeyboardButton("📥 Get File", url=file_unique_link)]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📥 Get File", url=file_unique_link)]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if target_update_channel.startswith("@" ) or target_update_channel.lstrip('-').isdigit():
            chat_to_send = int(target_update_channel) if target_update_channel.lstrip('-').isdigit() else target_update_channel
        else:
            chat_to_send = target_update_channel

        await context.bot.send_message(
            chat_id=chat_to_send,
            text=caption_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        logger.info(f"Auto post sent successfully to channel: {target_update_channel}!")
    except Exception as e:
        logger.error(f"Error sending auto post: {e}")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN is missing in Environment Variables!")
    
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()

    setup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^setup_channels$")],
        states={
            GET_UPDATE_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_update_channel_step)],
            GET_DB_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_db_channel_step)],
            GET_TARGET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_link_step)],
            GET_FILE_FORMAT: [CallbackQueryHandler(get_file_format_step, pattern="^fmt_")],
            GET_TOP_HEADING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_top_heading_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)]
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(setup_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL | filters.TEXT), auto_post_handler))

    print("Bot is running with fully corrected setup steps and advanced file name cleaning...")
    app.run_polling()

if __name__ == "__main__":
    main()
                           
