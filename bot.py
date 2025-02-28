from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
import logging
import pytz
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import asyncio

# إعدادات البوت
TOKEN = "7712506538:AAHgFTEg7_fuhq0sTN2dwZ88UFV1iQ6ycQ4"
CHANNEL_ID = "@jordangold"
TIMEZONE = pytz.timezone("Asia/Riyadh")

# إعداد السجلات لمراقبة الأخطاء
logging.basicConfig(level=logging.INFO)

# دالة لجلب الأحداث الاقتصادية مع تحسينات

def fetch_economic_events():
    url = "https://sa.investing.com/economic-calendar"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # فحص الاستجابة
        soup = BeautifulSoup(response.text, "html.parser")
        events = []
        rows = soup.find_all("tr", class_="js-event-item")

        if not rows:
            logging.warning("⚠️ لم يتم العثور على أي أحداث. قد يكون الموقع قد غير هيكله.")
            return []

        for row in rows:
            try:
                event_time = row.find("td", class_="first left time js-time").text.strip()
                event_name = row.find("td", class_="left event").text.strip()
                event_country = row.find("td", class_="flagCur").get("title", "غير معروف")
                event_impact = row.find("td", class_="left textNum sentiment noWrap").text.strip()
                
                if "USA" in event_country or "الولايات المتحدة" in event_country:
                    events.append({
                        'time': event_time,
                        'name': event_name,
                        'country': event_country,
                        'impact': event_impact
                    })
            except Exception as e:
                logging.error(f"❌ خطأ في تحليل حدث: {e}")

        return events
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ فشل الاتصال بـ Investing.com: {e}")
        return []

# دالة لإرسال الأحداث إلى قناة تيليجرام
async def send_event_to_channel(bot: Bot, event):
    try:
        message = f"\U0001F4C5 الحدث: {event['name']}\n⏰ التوقيت: {event['time']}\n\U0001F6A8 التأثير: {event['impact']}\n"
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
        logging.info(f"تم إرسال الحدث: {event['name']} إلى القناة")
    except Exception as e:
        logging.error(f"خطأ في إرسال الحدث {event['name']}: {e}")

# دالة جدولة إرسال الأحداث قبل 15 دقيقة من موعدها
async def schedule_events(bot: Bot):
    while True:
        events = fetch_economic_events()
        logging.info(f"تم جلب {len(events)} حدثًا اقتصاديًا")
        now = datetime.now(TIMEZONE)
        for event in events:
            try:
                event_time = datetime.strptime(event['time'], "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
                time_diff = event_time - timedelta(minutes=15)
                if now >= time_diff and now <= event_time:
                    await send_event_to_channel(bot, event)
            except Exception as e:
                logging.error(f"خطأ في جدولة الحدث: {e}")
        await asyncio.sleep(60)  # التحقق كل دقيقة

# دالة تشغيل البوت
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ تم تشغيل البوت بنجاح! سيتم إرسال الأحداث الاقتصادية تلقائيًا.")
    bot = context.bot
    events = fetch_economic_events()
    for event in events:
        await send_event_to_channel(bot, event)

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    bot = Bot(TOKEN)
    asyncio.create_task(schedule_events(bot))  # تجنب مشاكل event loop
    logging.info("✅ البوت يعمل بنجاح!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
