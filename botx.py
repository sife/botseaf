from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
import logging
import pytz
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import asyncio
import os

# إعدادات البوت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHANNEL_ID = "@jordangold"
TIMEZONE = pytz.timezone("Asia/Riyadh")

# إعداد السجلات لمراقبة الأخطاء
logging.basicConfig(level=logging.INFO)

# دالة لجلب الأحداث الاقتصادية بدون Selenium
def fetch_economic_events():
    url = "https://sa.investing.com/economic-calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logging.error(f"خطأ أثناء جلب الصفحة: {e}")
        return []

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
            logging.error(f"خطأ في تحليل الحدث: {e}")
            continue
    
    return events

# دالة لتحليل الوقت من تنسيق الحدث
def parse_event_time(event_time_str):
    try:
        return datetime.strptime(event_time_str, "%I:%M %p")
    except Exception as e:
        logging.warning(f"التنسيق غير صالح للوقت: {event_time_str} - {e}")
        return None

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
            event_time = parse_event_time(event['time'])
            if event_time:
                event_time = event_time.replace(year=now.year, month=now.month, day=now.day)
                time_diff = event_time - timedelta(minutes=15)
                if now >= time_diff and now <= event_time:
                    logging.info(f"إرسال الحدث: {event['name']} في التوقيت المحدد")
                    await send_event_to_channel(bot, event)

        await asyncio.sleep(60)  # التحقق كل دقيقة

# دالة بدء البوت
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ تم تشغيل البوت بنجاح! سيتم إرسال الأحداث الاقتصادية تلقائيًا.")
    bot = context.bot
    events = fetch_economic_events()
    logging.info(f"تم جلب {len(events)} حدثًا اقتصاديًا")
    
    for event in events:
        await send_event_to_channel(bot, event)

# تشغيل البوت
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    bot = Bot(TOKEN)

    loop = asyncio.get_running_loop()  # استخدام get_running_loop بدلاً من run
    loop.create_task(schedule_events(bot))  # تشغيل الجدولة دون إيقاف الحدث الرئيسي

    logging.info("✅ البوت يعمل بنجاح!")
    await application.run_polling()  # بدء العمل مع البوت

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main())  # تشغيل `main()` داخل الحلقة الحالية
