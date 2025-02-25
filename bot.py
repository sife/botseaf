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
TOKEN = "7712506538:AAHgFTEg7_fuhq0sTN2dwZ88UFV1iQ6ycQ4"
CHANNEL_ID = "@testbotseaf"
TIMEZONE = pytz.timezone("Asia/Riyadh")

# إعداد السجلات لمراقبة الأخطاء
logging.basicConfig(level=logging.INFO)

# دالة لجلب الأحداث الاقتصادية بدون Selenium

def fetch_economic_events():
    url = "https://sa.investing.com/economic-calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    events = []
    rows = soup.find_all("tr", class_="js-event-item")
    
    for row in rows:
        try:
            event_time = row.find("td", class_="left time").text.strip()
            event_name = row.find("td", class_="left event").text.strip()
            event_country = row.find("td", class_="flagCur").text.strip()
            event_impact = row.find("td", class_="sentiment").text.strip()
            
            if "USA" in event_country:
                event = {
                    'time': event_time,
                    'name': event_name,
                    'country': event_country,
                    'impact': event_impact
                }
                events.append(event)
        except:
            continue
    
    return events

# دالة لإرسال الأحداث إلى قناة تيليجرام
async def send_event_to_channel(bot: Bot, event):
    message = f"\U0001F4C5 الحدث: {event['name']}\n⏰ التوقيت: {event['time']}\n\U0001F6A8 التأثير: {event['impact']}\n"
    await bot.send_message(chat_id=CHANNEL_ID, text=message)

# دالة تشغيل البوت وإرسال الأحداث عند التشغيل
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ تم تشغيل البوت بنجاح! سيتم إرسال الأحداث الاقتصادية تلقائيًا.")
    bot = context.bot
    events = fetch_economic_events()
    for event in events:
        await send_event_to_channel(bot, event)

# جدولة إرسال الأحداث قبل 15 دقيقة من موعدها
async def schedule_events(bot: Bot):
    while True:
        events = fetch_economic_events()
        now = datetime.now(TIMEZONE)
        for event in events:
            try:
                event_time = datetime.strptime(event['time'], "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
                time_diff = event_time - timedelta(minutes=15)
                if now >= time_diff:
                    await send_event_to_channel(bot, event)
            except Exception as e:
                logging.error(f"خطأ في جدولة الحدث: {e}")
        await asyncio.sleep(60)  # التحقق كل دقيقة

# تشغيل البوت
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    bot = Bot(TOKEN)
    asyncio.create_task(schedule_events(bot))
    print("✅ البوت يعمل بنجاح!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
