from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
import logging
import pytz
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import asyncio

# إعدادات البوت
TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_ID = "@jordangold"
TIMEZONE = pytz.timezone("Asia/Riyadh")

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# دالة لجلب الأحداث الاقتصادية
def fetch_economic_events():
    url = "https://sa.investing.com/economic-calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    events = []
    rows = soup.find_all("tr", class_="js-event-item")
    
    for row in rows:
        try:
            event_time = row.find("td", class_="first left time js-time")
            event_time = event_time.text.strip() if event_time else "غير محدد"

            event_name = row.find("td", class_="left event")
            event_name = event_name.text.strip() if event_name else "غير محدد"

            event_country = row.find("td", class_="flagCur")
            event_country = "الولايات المتحدة" if event_country and "United_States" in event_country.get("class", []) else "غير محدد"

            event_impact = row.find("td", class_="left textNum sentiment noWrap")
            event_impact = event_impact.text.strip() if event_impact else "غير محدد"

            if event_country == "الولايات المتحدة":
                events.append({'time': event_time, 'name': event_name, 'impact': event_impact})

        except Exception as e:
            logging.error(f"خطأ في جلب الحدث: {e}")
    
    return events

# دالة تحليل الوقت
def parse_event_time(event_time_str):
    try:
        return datetime.strptime(event_time_str, "%I:%M %p")
    except Exception as e:
        logging.warning(f"التنسيق غير صالح للوقت: {event_time_str} - {e}")
        return None

# دالة لإرسال الأحداث إلى تيليجرام
async def send_event_to_channel(bot: Bot, event):
    try:
        message = f"\U0001F4C5 الحدث: {event['name']}\n⏰ التوقيت: {event['time']}\n\U0001F6A8 التأثير: {event['impact']}\n"
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
        logging.info(f"تم إرسال الحدث: {event['name']} إلى القناة")
    except Exception as e:
        logging.error(f"خطأ في إرسال الحدث {event['name']}: {e}")

# دالة جدولة الأحداث
async def schedule_events(bot: Bot):
    while True:
        events = fetch_economic_events()
        logging.info(f"تم جلب {len(events)} حدثًا اقتصاديًا")
        now = datetime.now(TIMEZONE)
        
        for event in events:
            event_time = parse_event_time(event['time'])
            if event_time:
                event_time = event_time.replace(year=now.year, month=now.month, day=now.day)
                if now >= event_time - timedelta(minutes=15) and now <= event_time:
                    await send_event_to_channel(bot, event)

        await asyncio.sleep(60)  # تحديث كل دقيقة

# دالة تشغيل البوت
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ تم تشغيل البوت بنجاح! سيتم إرسال الأحداث الاقتصادية تلقائيًا.")
    bot = context.bot
    for event in fetch_economic_events():
        await send_event_to_channel(bot, event)

# تشغيل البوت
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    bot = Bot(TOKEN)

    # تشغيل جدولة الأحداث
    asyncio.create_task(schedule_events(bot))
    
    logging.info("✅ البوت يعمل بنجاح!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())  # استخدام asyncio.run() بدلاً من get_event_loop()
