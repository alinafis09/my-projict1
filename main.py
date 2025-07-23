import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI
import aiohttp
from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY

# إعداد السجل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد عميل OpenAI
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحبًا! أنا بوت ذكاء اصطناعي. أرسل لي رسالة أو جرب /yts للبحث في يوتيوب.")

# أمر /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - بدء المحادثة\n"
        "/help - المساعدة\n"
        "/yts [الكلمة] - البحث في يوتيوب\n"
        "أرسل أي رسالة وسأرد باستخدام الذكاء الاصطناعي!"
    )

# استجابة الذكاء الاصطناعي
async def get_openai_response(message: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"خطأ في الذكاء الاصطناعي: {e}")
        return "❌ حدث خطأ في الذكاء الاصطناعي. حاول لاحقًا."

# أمر /yts للبحث في يوتيوب
async def youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 اكتب بعد الأمر ما تريد البحث عنه، مثل:\n/yts lo-fi music")
        return

    query = " ".join(context.args)
    await update.message.reply_text("🔍 جاري البحث عن: " + query)

    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as resp:
                html = await resp.text()

        import re
        matches = re.findall(r"watch\?v=(\S{11})", html)
        if matches:
            video_id = matches[0]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
            await update.message.reply_photo(photo=thumbnail_url, caption=f"📺 {query}\n{video_url}")
        else:
            await update.message.reply_text("❌ لم أتمكن من العثور على نتائج.")
    except Exception as e:
        logger.error(f"خطأ في البحث باليوتيوب: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء البحث في اليوتيوب.")

# الرد على أي رسالة بالذكاء الاصطناعي
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user.first_name
    logger.info(f"📩 رسالة من {user}: {text}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await get_openai_response(text)
    await update.message.reply_text(response)

# التعامل مع الأخطاء
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"❗ حدث خطأ: {context.error}")

# تشغيل البوت
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("yts", youtube_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("✅ البوت شغال الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
