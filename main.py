import logging
import os
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ലോഗിങ് സെറ്റ് ചെയ്യുക
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(name)

# ഡാറ്റാബേസ് ചാനൽ ഐടിയും അപ്ഡേറ്റ്സ് ചാനൽ ഐടിയും
DATABASE_CHANNEL_ID = -1004396151945
UPDATES_CHANNEL_ID = -1002110922261

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

        # സീരിയലിന്റെ പേര് ക്ലീൻ ചെയ്ത് എടുക്കുന്നു (ഉദാഹരണത്തിന്: Kudumbasametham അല്ലെങ്കിൽ Kudumbashree Sharada)
        title_clean = re.sub(r's0?\d+|ep?\s*\d+|episode|\b480p\b|\b720p\b|\b1080p\b', '', clean_name, flags=re.IGNORECASE).strip()
        if not title_clean:
            title_clean = "h"

        # സ്ക്രീൻഷോട്ടിലുള്ളതുപോലുള്ള ക്യാപ്ഷൻ ഡിസൈൻ
        caption_text = (
            f"<b>🍁𝑨𝒏𝒖𝒋𝒊𝒕𝒉 𝑨𝒍𝒍𝒖 𝑻𝑽 𝑺𝒆𝒓𝒊𝒂𝒍𝒔🍁</b>\n"
            f"📁 <b>File Name :</b> {title_clean}\n"
            f"🎞 <b>Season :</b> {season.zfill(2)}\n"
            f"📌 <b>Episode :</b> {episode}\n"
            f"🎬 <b>Quality :</b> {quality}"
        )

        # നിങ്ങൾ ആവശ്യപ്പെട്ടതുപോലെ സീരിയലിന്റെ പേരും സീസൺ/എപ്പിസോഡും ചേർന്ന് ലിങ്ക് രൂപപ്പെടുന്നു 
        # (ഉദാഹരണത്തിന്: https://telegram.me/Anujith1bot?start=getfile-Kudumbasametham-S01E536)
        formatted_title_for_link = title_clean.replace(" ", "")
        file_unique_link = f"https://telegram.me/Anujith1bot?start=getfile-{formatted_title_for_link}-S{season.zfill(2)}E{episode}"
        
        # ബട്ടണിൽ "Get File" എന്ന് മാത്രം കാണിക്കുന്നു
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

    # ഡാറ്റാബേസ് ചാനൽ നിരീക്ഷിക്കുന്നു
    app.add_handler(MessageHandler(filters.Chat(DATABASE_CHANNEL_ID) & (filters.VIDEO | filters.Document.ALL | filters.TEXT), auto_post_handler))

    print("Custom Link Auto Post Bot is running...")
    app.run_polling()

if name == "main":
    main()
