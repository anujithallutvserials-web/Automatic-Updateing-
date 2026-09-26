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
GET_UPDATE_CHANNEL, GET_DB_CHANNEL, GET_TARGET_LINK, GET_FILE_FORMAT, GET_BANNER_URL, GET_TOP_HEADING = range(6)

# --- SERIALS MAPPING & GET FILE LINKS ---
SERIALS_MAPPING = {
    "kanmashi": "Kanmashi",
    "karnan": "Karnan",
    "valyettan": "Valyettan",
    "pranayavilasam": "Pranayavilasam",
    "durga": "Durga",
    "chembarathy": "Chembarathy",
    "saregamapa": "SaReGaMaPa",
    "saregamapa-lil-champs": "SaReGaMaPa Lil Champs",
    "kudumbasametham": "Kudumbasametham",
    "meghasandhesham": "Meghasandhesham",
    "seethayanam": "Seethayanam",
    "krishnagadha": "Krishnagadha",
    "meghasandesam": "Meghasandesam",
    "aval-arundhati": "Aval Arundhati",
    "akale": "Akale",
    "snehapoorvam-shyama": "Snehapoorvam Shyama",
    "mangalyam": "Mangalyam",
    "manathe-kottaram": "Manathe Kottaram",
    "ashwathi-nakshatram": "Ashwathi Nakshatram",
    "kudumbashree-sharada": "Kudumbashree Sharada",
    "bigg-boss": "Bigg Boss",
    "taste-time": "Taste Time",
    "sindhu-bhairavi": "Sindhu Bhairavi",
    "comedy-cooks": "Comedy Cooks",
    "ivar-vivahitharayal": "Ivar Vivahitharayal",
    "oru-kochu-swapnam": "Oru Kochu Swapnam",
    "advocate-anjali": "Advocate Anjali",
    "kattathe-kilikoodu": "Kattathe Kilikoodu",
    "ee-puzhayum-kadannu": "Ee Puzhayum Kadannu",
    "sindoorapottu": "Sindoorapottu",
    "star-singer": "Star Singer",
    "teacheramma": "Teacheramma",
    "mazha-thorum-munpe": "Mazha Thorum Munpe",
    "pavithram": "Pavithram",
    "ishtam-mathram": "Ishtam Mathram",
    "santhwanam": "Santhwanam",
    "snehakkoottu": "Snehakkoottu",
    "mounaragam": "Mounaragam",
    "patharamattu": "Patharamattu",
    "amma-manassu": "Amma Manassu",
    "chempaneer-poovu": "Chempaneer Poovu",
    "dharmma-yoddhavu-garudan": "Dharmma Yoddhavu Garudan",
    "othiri-othiri-swapnangal": "Othiri Othiri Swapnangal",
    "ottashikharam": "Ottashikharam",
    "archana-chechi-llb": "Archana Chechi LLB",
    "super-kanmani": "Super Kanmani",
    "marimayam": "Marimayam",
    "oru-chiri-iru-chiri-bumper-chiri": "Oru Chiri Iru Chiri Bumper Chiri",
    "the-great-family-challenge": "The Great Family Challenge",
    "roopavathi": "Roopavathi",
    "thenmavin-kombath": "Thenmavin Kombath",
    "punnaram": "Punnaram",
    "anju-sundarikal": "Anju Sundarikal",
    "amme-mookambike": "Amme Mookambike",
    "peythozhiyathe": "Peythozhiyathe",
    "chattambipparu": "Chattambipparu",
    "hridayam": "Hridayam",
    "kanyadaanam": "Kanyadaanam",
    "swayamavarapanthal": "Swayamavarapanthal",
    "mangalyam-thanthunanena": "Mangalyam Thanthunanena"
}

GET_FILE_LINKS = [
    "https://telegram.me/Anujith1bot?start=getfile-Kanmashi",
    "https://telegram.me/Anujith1bot?start=getfile-Karnan",
    "https://telegram.me/Anujith1bot?start=getfile-Valyettan",
    "https://telegram.me/Anujith1bot?start=getfile-Pranayavilasam",
    "https://telegram.me/Anujith1bot?start=getfile-Durga",
    "https://telegram.me/Anujith1bot?start=getfile-Chembarathy",
    "https://telegram.me/Anujith1bot?start=getfile-SaReGaMaPa",
    "https://telegram.me/Anujith1bot?start=getfile-SaReGaMaPa-Lil-Champs",
    "https://telegram.me/Anujith1bot?start=getfile-Kudumbasametham",
    "https://telegram.me/Anujith1bot?start=getfile-Meghasandhesham",
    "https://telegram.me/Anujith1bot?start=getfile-Seethayanam",
    "https://telegram.me/Anujith1bot?start=getfile-Krishnagadha",
    "https://telegram.me/Anujith1bot?start=getfile-Meghasandesam",
    "https://telegram.me/Anujith1bot?start=getfile-Aval-Arundhati",
    "https://telegram.me/Anujith1bot?start=getfile-Akale",
    "https://telegram.me/Anujith1bot?start=getfile-Snehapoorvam-Shyama",
    "https://telegram.me/Anujith1bot?start=getfile-Mangalyam",
    "https://telegram.me/Anujith1bot?start=getfile-Manathe-Kottaram",
    "https://telegram.me/Anujith1bot?start=getfile-Ashwathi-Nakshatram",
    "https://telegram.me/Anujith1bot?start=getfile-Kudumbashree-Sharada",
    "https://telegram.me/Anujith1bot?start=getfile-Bigg-Boss",
    "https://telegram.me/Anujith1bot?start=getfile-Taste-Time",
    "https://telegram.me/Anujith1bot?start=getfile-Sindhu-Bhairavi",
    "https://telegram.me/Anujith1bot?start=getfile-Comedy-Cooks",
    "https://telegram.me/Anujith1bot?start=getfile-Ivar-Vivahitharayal",
    "https://telegram.me/Anujith1bot?start=getfile-Oru-Kochu-Swapnam",
    "https://telegram.me/Anujith1bot?start=getfile-Advocate-Anjali",
    "https://telegram.me/Anujith1bot?start=getfile-Kattathe-Kilikoodu",
    "https://telegram.me/Anujith1bot?start=getfile-Ee-Puzhayum-Kadannu",
    "https://telegram.me/Anujith1bot?start=getfile-Sindoorapottu",
    "https://telegram.me/Anujith1bot?start=getfile-Star-Singer",
    "https://telegram.me/Anujith1bot?start=getfile-Teacheramma",
    "https://telegram.me/Anujith1bot?start=getfile-Mazha-Thorum-Munpe",
    "https://telegram.me/Anujith1bot?start=getfile-Pavithram",
    "https://telegram.me/Anujith1bot?start=getfile-Ishtam-Mathram",
    "https://telegram.me/Anujith1bot?start=getfile-Santhwanam",
    "https://telegram.me/Anujith1bot?start=getfile-Snehakkoottu",
    "https://telegram.me/Anujith1bot?start=getfile-Mounaragam",
    "https://telegram.me/Anujith1bot?start=getfile-Patharamattu",
    "https://telegram.me/Anujith1bot?start=getfile-Amma-Manassu",
    "https://telegram.me/Anujith1bot?start=getfile-Chempaneer-Poovu",
    "https://telegram.me/Anujith1bot?start=getfile-Dharmma-Yoddhavu-Garudan",
    "https://telegram.me/Anujith1bot?start=getfile-Othiri-Othiri-Swapnangal",
    "https://telegram.me/Anujith1bot?start=getfile-Ottashikharam",
    "https://telegram.me/Anujith1bot?start=getfile-Archana-Chechi-LLB",
    "https://telegram.me/Anujith1bot?start=getfile-Super-Kanmani",
    "https://telegram.me/Anujith1bot?start=getfile-Marimayam",
    "https://telegram.me/Anujith1bot?start=getfile-Oru-Chiri-Iru-Chiri-Bumper-Chiri",
    "https://telegram.me/Anujith1bot?start=getfile-The-Great-Family-Challenge",
    "https://telegram.me/Anujith1bot?start=getfile-Roopavathi",
    "https://telegram.me/Anujith1bot?start=getfile-Thenmavin-Kombath",
    "https://telegram.me/Anujith1bot?start=getfile-Punnaram",
    "https://telegram.me/Anujith1bot?start=getfile-Anju-Sundarikal",
    "https://telegram.me/Anujith1bot?start=getfile-Amme-Mookambike",
    "https://telegram.me/Anujith1bot?start=getfile-Peythozhiyathe",
    "https://telegram.me/Anujith1bot?start=getfile-Chattambipparu",
    "https://telegram.me/Anujith1bot?start=getfile-Hridayam",
    "https://telegram.me/Anujith1bot?start=getfile-Kanyadaanam",
    "https://telegram.me/Anujith1bot?start=getfile-Swayamavarapanthal",
    "https://telegram.me/Anujith1bot?start=getfile-Mangalyam-Thanthunanena"
]
# ----------------------------------------

# --- SQLITE DATABASE SETUP (MULTI-CHANNEL SUPPORT) ---
def init_db():
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            update_channel TEXT,
            db_channel INTEGER,
            target_link TEXT,
            file_format TEXT,
            banner_url TEXT,
            top_heading TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_user_config(user_id, update_channel, db_channel, target_link, file_format, banner_url, top_heading):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO configs (user_id, update_channel, db_channel, target_link, file_format, banner_url, top_heading)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, update_channel, db_channel, target_link, file_format, banner_url, top_heading))
    conn.commit()
    conn.close()

def get_user_configs(user_id):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, update_channel, db_channel, target_link, file_format, banner_url, top_heading FROM configs WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_config_by_id(config_id):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, update_channel, db_channel, target_link, file_format, banner_url, top_heading FROM configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_config_by_id(config_id):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM configs WHERE id = ?', (config_id,))
    conn.commit()
    conn.close()

def get_config_by_db(db_channel):
    conn = sqlite3.connect('bot_configs.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, update_channel, target_link, file_format, banner_url, top_heading FROM configs WHERE db_channel = ?', (db_channel,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1], row[2], row[3], row[4], row[5]
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

    user_id = update.effective_user.id
    configs = get_user_configs(user_id)

    welcome_text = (
        "👋 Welcome to the <b>Automatic Update & Media Bot</b>!\n\n"
        "This bot helps you automatically format and forward your serial updates, videos, and files to your target update channels cleanly and professionally.\n\n"
        "<b>Key Features & Formats:</b>\n"
        "• <b>Photo Format (Banner + Details):</b> Sends a custom banner image at the top followed by details and an interactive button below it.\n"
        "• <b>Video Format:</b> Forwards the video file directly with clean formatting and buttons.\n"
        "• <b>Text Format:</b> Sends text-based updates with custom headings and target buttons.\n\n"
        "Select your configured channel below or click <b>'+ Add Channel'</b> to add a new one."
    )
    
    keyboard = []
    for cfg in configs:
        cfg_id, update_ch, _, _, _, _, _ = cfg
        keyboard.append([InlineKeyboardButton(f"📢 {update_ch}", callback_data=f"manage_cfg_{cfg_id}")])
    
    keyboard.append([InlineKeyboardButton("➕ Add Channel", callback_data="setup_channels")])
    keyboard.append([InlineKeyboardButton("❓ Help & Instructions", callback_data="help_menu")])
    keyboard.append([InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_text = (
        "👑 <b>Admin Information</b>\n\n"
        "If you need any support or want to contact the admin, please reach out to:\n"
        "💬 <b>Contact:</b> @Anujith1238"
    )
    keyboard = [[InlineKeyboardButton("👤 Chat with Admin", url="https://t.me/Anujith1238")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 <b>Bot Help & Instructions Menu</b>\n\n"
        "How to use this bot properly:\n\n"
        "1️⃣ <b>Updates Channel:</b> First send your target Updates Channel ID or Username (e.g., <code>-100xxxxxxxxxx</code> or <code>@yourchannel</code>).\n"
        "2️⃣ <b>Database Channel:</b> Send your source Database Channel ID where raw files are uploaded.\n"
        "3️⃣ <b>Target Link/ID:</b> Provide the destination link or ID that will be attached to the 'Get File' button.\n"
        "4️⃣ <b>File Format Selection:</b> Choose how your posts should look:\n"
        "   - <i>Photo Format (Banner + Details):</i> Displays a banner image at the top with formatted details below.\n"
        "   - <i>Video Format:</i> Forwards the actual video with a clean caption.\n"
        "   - <i>Text Format:</i> Sends a text update message.\n"
        "5️⃣ <b>Banner Image URL:</b> If Photo format is chosen, provide a direct image link to serve as the banner background/header.\n"
        "6️⃣ <b>Top Heading:</b> Enter your custom title/heading to appear at the top of every post.\n\n"
        "💬 <b>Need Help? Contact Owner:</b> @Anujith1238"
    )
    keyboard = [[InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "setup_channels":
        await query.message.edit_text(
            "⚙️ <b>Channel Setup Wizard</b>\n\n"
            "1️⃣ Please send your <b>Updates Channel ID</b> or Username (e.g., <code>-100xxxxxxxxxx</code> or <code>@yourchannel</code>):",
            parse_mode="HTML"
        )
        return GET_UPDATE_CHANNEL

    elif query.data.startswith("manage_cfg_"):
        cfg_id = int(query.data.split("_")[2])
        cfg = get_config_by_id(cfg_id)
        if not cfg:
            await query.message.edit_text("❌ Configuration not found.")
            return

        _, _, update_ch, db_ch, target_l, f_fmt, banner_u, top_h = cfg
        details_text = (
            "⚙️ <b>Channel Configuration Details</b>\n\n"
            f"📢 <b>Updates Channel:</b> <code>{update_ch}</code>\n"
            f"📁 <b>Database Channel:</b> <code>{db_ch}</code>\n"
            f"🔗 <b>Target Link/ID:</b> <code>{target_l}</code>\n"
            f"📄 <b>File Format:</b> <code>{f_fmt}</code>\n"
            f"🖼 <b>Banner URL:</b> {banner_u if banner_u else 'None'}\n"
            f"🏷 <b>Top Heading:</b> {top_h}"
        )
        keyboard = [
            [InlineKeyboardButton("🗑 Remove Channel", callback_data=f"remove_cfg_{cfg_id}")],
            [InlineKeyboardButton("« Back", callback_data="back_home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(details_text, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data.startswith("remove_cfg_"):
        cfg_id = int(query.data.split("_")[2])
        delete_config_by_id(cfg_id)
        await query.message.edit_text("✅ Channel configuration removed successfully!")
        await start_command(update, context)

    elif query.data == "help_menu":
        help_text = (
            "🤖 <b>Bot Help & Instructions Menu</b>\n\n"
            "How to use this bot properly:\n\n"
            "1️⃣ <b>Updates Channel:</b> Send your target Updates Channel ID.\n"
            "2️⃣ <b>Database Channel:</b> Send your Database Channel ID.\n"
            "3️⃣ <b>Target Link/ID:</b> Provide link for the button.\n"
            "4️⃣ <b>File Format:</b> Select Photo, Video, or Text format.\n"
            "5️⃣ <b>Banner Image URL:</b> Provide direct image link for photo banners.\n"
            "6️⃣ <b>Top Heading:</b> Enter custom heading for your posts.\n\n"
            "💬 <b>Contact Owner:</b> @Anujith1238"
        )
        keyboard = [
            [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")],
            [InlineKeyboardButton("« Back", callback_data="back_home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back_home":
        await start_command(update, context)

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
            "2️⃣ Now, please send your <b>Database Channel ID</b> (e.g., <code>-100xxxxxxxxxx</code>):",
            parse_mode="HTML"
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
            "3️⃣ Now, send your target link/ID for the Get File button:",
            parse_mode="HTML"
        )
        return GET_TARGET_LINK
    except ValueError:
        await update.message.reply_text("❌ Invalid ID! Please send a valid numeric Database Channel ID:")
        return GET_DB_CHANNEL

async def get_target_link_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_link_input = update.message.text.strip()
    context.user_data['temp_target_link'] = target_link_input

    keyboard = [
        [InlineKeyboardButton("🖼 Photo Format (Banner + Details)", callback_data="fmt_photo")],
        [InlineKeyboardButton("📄 Text Format", callback_data="fmt_text")],
        [InlineKeyboardButton("🎬 Video Format", callback_data="fmt_video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Target Link/ID saved successfully!\n\n"
        "4️⃣ Please select your preferred <b>File Format</b>:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return GET_FILE_FORMAT

async def get_file_format_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    fmt_choice = query.data
    if fmt_choice == "fmt_photo":
        context.user_data['temp_file_format'] = "Photo"
        await query.message.edit_text(
            "✅ Photo Format selected!\n\n"
            "5️⃣ Please send the <b>Banner Image URL</b> (Send a direct image link/URL to use as the banner header):",
            parse_mode="HTML"
        )
        return GET_BANNER_URL
    else:
        context.user_data['temp_file_format'] = "Text" if fmt_choice == "fmt_text" else "Video"
        context.user_data['temp_banner_url'] = ""
        await query.message.edit_text(
            "✅ File Format saved successfully!\n\n"
            "6️⃣ Finally, please type and send your custom <b>Top Heading</b> text:",
            parse_mode="HTML"
        )
        return GET_TOP_HEADING

async def get_banner_url_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banner_url = update.message.text.strip()
    context.user_data['temp_banner_url'] = banner_url

    await update.message.reply_text(
        "✅ Banner Image URL saved successfully!\n\n"
        "6️⃣ Finally, please type and send your custom <b>Top Heading</b> text:",
        parse_mode="HTML"
    )
    return GET_TOP_HEADING

async def get_top_heading_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    top_heading = update.message.text.strip()

    update_channel = context.user_data.get('temp_update_channel')
    db_channel = context.user_data.get('temp_db_channel')
    target_link = context.user_data.get('temp_target_link')
    file_format = context.user_data.get('temp_file_format')
    banner_url = context.user_data.get('temp_banner_url', '')

    save_user_config(user_id, update_channel, db_channel, target_link, file_format, banner_url, top_heading)

    success_msg = (
        "🎉 <b>Setup Successful! Channel Added.</b>\n\n"
        f"📢 <b>Updates Channel:</b> <code>{update_channel}</code>\n"
        f"📁 <b>Database Channel:</b> <code>{db_channel}</code>\n"
        f"🔗 <b>Target Link/ID:</b> <code>{target_link}</code>\n"
        f"⚙️ <b>File Format:</b> <code>{file_format}</code>\n"
        f"🖼 <b>Banner URL:</b> {banner_url if banner_url else 'None'}\n"
        f"🏷 <b>Top Heading:</b> {top_heading}"
    )

    keyboard = [[InlineKeyboardButton("« Go to Home / Channels", callback_data="back_home")]]
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

    user_id, target_update_channel, target_link, file_format, banner_url, top_heading = config

    file_name = ""
    if message.document:
        file_name = message.document.file_name
    elif message.video:
        file_name = message.video.file_name or message.caption or "Unknown Video"
    elif message.caption:
        file_name = message.caption

    if not file_name:
        return

    file_name_lower = file_name.lower()
    
    detected_serial = None
    matched_key = None
    
    for key, serial_name in SERIALS_MAPPING.items():
        formatted_key = key.replace("-", " ")
        if formatted_key in file_name_lower or key in file_name_lower:
            detected_serial = serial_name
            matched_key = key
            break
            
    if not detected_serial:
        detected_serial = os.path.splitext(file_name)[0]

    season_match = re.search(r'S(\d+)', file_name, re.IGNORECASE)
    season = season_match.group(1) if season_match else "-"
    
    episode_match = re.findall(r'E(\d+(?:-\d+)?)', file_name, re.IGNORECASE)
    if not episode_match:
        episode_match = re.findall(r'(\d+-\d+)', file_name)
    if not episode_match:
        episode_match = re.findall(r'Episode[_\s.-]*(\d+(?:-\d+)?)', file_name, re.IGNORECASE)
    if not episode_match:
        single_ep = re.findall(r'E(\d+)', file_name, re.IGNORECASE)
        if single_ep:
            episode_match = single_ep
            
    episode = episode_match[0] if episode_match else "-"

    qualities = re.findall(r'(\d{3,4}p)', file_name, re.IGNORECASE)
    if qualities:
        quality = " - ".join(sorted(list(set(qualities))))
    else:
        quality = "-"

    heading_to_show = top_heading if top_heading else "🍁 Anujith Allu TV Serials 🍁"

    caption_text = (
        f"<b>{heading_to_show}</b>\n\n"
        f"📁 <b>File Name :</b> {detected_serial}\n"
        f"🎞 <b>Season :</b> {season}\n"
        f"📌 <b>Episode :</b> {episode}\n"
        f"🎬 <b>Quality :</b> {quality}"
    )

    get_file_url = None
    if matched_key:
        for link in GET_FILE_LINKS:
            if matched_key.replace("-", "").lower() in link.replace("-", "").lower():
                get_file_url = link
                break
    
    if not get_file_url:
        if target_link:
            encoded_title = quote(detected_serial)
            if target_link.startswith("https://"):
                get_file_url = f"{target_link.rstrip('/')}/{encoded_title}"
            elif target_link.startswith("@"):
                get_file_url = f"https://t.me/{target_link.lstrip('@')}"
            else:
                get_file_url = f"https://t.me/{target_link}"
        else:
            get_file_url = f"https://telegram.me/Anujith1bot?start=getfile-{detected_serial.replace(' ', '-')}"

    keyboard = [[InlineKeyboardButton("📥 Get File", url=get_file_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        chat_to_send = int(target_update_channel) if str(target_update_channel).lstrip('-').isdigit() else target_update_channel

        if file_format == "Photo" and banner_url:
            await context.bot.send_photo(
                chat_id=chat_to_send,
                photo=banner_url,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        elif file_format == "Video" and (message.video or message.document):
            await context.bot.copy_message(
                chat_id=chat_to_send,
                from_chat_id=incoming_chat_id,
                message_id=message.message_id,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=chat_to_send,
                text=caption_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        logger.info("Auto post sent successfully!")
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
            GET_BANNER_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_banner_url_step)],
            GET_TOP_HEADING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_top_heading_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)]
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(setup_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL | filters.TEXT), auto_post_handler))

    print("Bot is running successfully with multi-channel management & English instructions...")
    app.run_polling()

if __name__ == "__main__":
    main()
