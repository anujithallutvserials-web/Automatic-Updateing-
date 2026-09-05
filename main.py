import logging
import os
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# ലോഗിങ് സെറ്റ് ചെയ്യുക
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ഡാറ്റാബേസ് ചാനൽ ഐടിയും അപ്ഡേറ്റ്സ് ചാനൽ ഐടിയും
DATABASE_CHANNEL_ID = -1004396151945
UPDATES_CHANNEL_ID = -1002110922261

# /start കമാൻഡ് അടിക്കുമ്പോൾ ബോട്ട് മറുപടി നൽകാൻ
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # സ്റ്റാർട്ട് ലിങ്കിൽ വരുന്ന ഫയൽ റിക്വസ്റ്റ് പരിശോധിക്കാൻ
    if context.args:
        payload = context.args[0]
        if payload.startswith("getfile-"):
            await update.message.reply_text(f"📥 You requested file details: `{payload}`\n\nFile delivery processing...")
            return

    # നിങ്ങൾ ആവശ്യപ്പെട്ട വെൽക്കം മെസ്സേജും ഹെൽപ്പ് ബട്ടണും
    welcome_text = "Hi, I am an automatically update bot"
    
    keyboard = [
        [InlineKeyboardButton("❓ Help / Contact Owner", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ഹെൽപ്പ് ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ വർക്ക് ചെയ്യുന്ന ഫങ്ഷൻ
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help_menu":
        help_text = (
            "🤖 **Bot Help Menu**\n\n"
            "This bot automatically updates and posts new media to the updates channel.\n\n"
            "💬 **Contact Owner:**\n"
            "If you have any questions or need support, contact: @Anujith1238"
        )
        
        # കോൺടാക്റ്റ് ചെയ്യാനുള്ള നേരിട്ടുള്ള ബട്ടൺ
        keyboard = [
            [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/Anujith1238")],
            [InlineKeyboardButton("« Back", callback_data="back_home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back_home":
        welcome_text = "Hi, I am an automatically update bot"
        keyboard = [
            [InlineKeyboardButton("❓ Help / Contact Owner", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(welcome_text, reply_markup=reply_markup)

# ഓട്ടോ പോസ്റ്റ് ഹാൻഡ്‌ലർ
async def auto_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post or update.message
    
    if not message:
        return

    # ഡാറ്റാബേസ് ചാനലിൽ നിന്ന് വരുന്ന ഫയലുകൾ പരിശോധിക്കുന്നു
    if message.chat.id == DATABASE_CHANNEL_ID:
        file_name = ""
        
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name or message.caption or "Unknown Video"
        elif message.caption:
            file_name = message.caption

        if not file_name:
            return

        # ഫയൽ പേരിൽ നിന്ന് വിവരങ്ങൾ വേർതിരിക്കുന്നു
        clean_name = file_name.replace("_", " ").replace(".", " ")
        
        # സീസൺ കണ്ടെത്താൻ (Default: 01)
        season_match = re.search(r's0?(\d+)', clean_name, re.IGNORECASE)
        season = season_match.group(1) if season_match else "01"
        
        # എപ്പിസോഡ് നമ്പർ കണ്ടെത്താൻ
        ep_match = re.search(r'(?:ep?|episode)\s*(\d+)', clean_name, re.IGNORECASE)
        if not ep_match:
            num_match = re.findall(r'\b\d{1,3}\b', clean_name)
            episode = num_match[-1] if num_match else "01"
        else:
            episode = ep_match.group(1)

        # ക്വാളിറ്റി കണ്ടെത്തുന്നു (720p, 1080p മുതലായവ)
        quality_match = re.search(r'(480p|720p|1080p)', clean_name, re.IGNORECASE)
        quality = quality_match.group(1) if quality_match else "720p"

        # സീരിയലിന്റെ പേര് ക്ലീൻ ചെയ്ത് എടുക്കുന്നു
        title_clean = re.sub(r's0?\d+|ep?\s*\d+|episode|\b480p\b|\b720p\b|\b1080p\b', '', clean_name, flags=re.IGNORECASE).strip()
        if not title_clean:
            title_clean = "Serial Video"

        # ക്യാപ്ഷൻ ഡിസൈൻ
        caption_text = (
            f"<b>🍁𝑨𝒏𝒖𝒋𝒊𝒕𝒉 𝑨𝒍𝒍𝒖 𝑻𝑽 𝑺𝒆𝒓𝒊𝒂𝒍𝒔🍁</b>\n"
            f"📁 <b>File Name :</b> {title_clean}\n"
            f"🎞 <b>Season :</b> {season.zfill(2)}\n"
            f"📌 <b>Episode :</b> {episode}\n"
            f"🎬 <b>Quality :</b> {quality}"
        )

        # ബട്ടൺ ലിങ്ക് രൂപപ്പെടുന്നു
        formatted_title_for_link = title_clean.replace(" ", "")
        file_unique_link = f"https://telegram.me/Anujith1bot?start=getfile-{formatted_title_for_link}-S{season.zfill(2)}E{episode}"
        
        keyboard = [
            [InlineKeyboardButton("📥 Get File", url=file_unique_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            # അപ്ഡേറ്റ്സ് ചാനലിലേക്ക് അയക്കുന്നു
            if message.video:
                await context.bot.send_video(
                    chat_id=UPDATES_CHANNEL_ID,
                    video=message.video.file_id,
                    caption=caption_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=UPDATES_CHANNEL_ID,
                    document=message.document.file_id,
                    caption=caption_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=UPDATES_CHANNEL_ID,
                    text=caption_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            logger.info("Auto post with clean custom link sent successfully!")
        except Exception as e:
            logger.error(f"Error sending auto post: {e}")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN is missing in Environment Variables!")
    
    app = ApplicationBuilder().token(TOKEN).build()

    # /start കമാൻഡ് ഹാൻഡ്‌ലർ
    app.add_handler(CommandHandler("start", start_command))
    
    # ഇൻലൈൻ ബട്ടൺ വർക്ക് ചെയ്യാനുള്ള ഹാൻഡ്‌ലർ
    app.add_handler(CallbackQueryHandler(button_handler))

    # ഡാറ്റാബേസ് ചാനൽ നിരീക്ഷിക്കുന്ന ഹാൻഡ്‌ലർ
    app.add_handler(MessageHandler(filters.Chat(DATABASE_CHANNEL_ID) & (filters.VIDEO | filters.Document.ALL | filters.TEXT), auto_post_handler))

    print("Bot with Help & Contact button is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
