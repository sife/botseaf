import telebot
import requests
from datetime import datetime, timedelta
import time

# بيانات البوت
TOKEN = "7712506538:AAHgFTEg7_fuhq0sTN2dwZ88UFV1iQ6ycQ4"
CHANNEL_ID = "@testbotseaf"
bot = telebot.TeleBot(TOKEN)

# رابط API للتقويم الاقتصادي
ECONOMY_API_URL = "https://api.investing.com/api/financialcalendar"
HEADERS = {
    "Content-Type": "application/json",
}

# جلب البيانات الاقتصادية
def get_economic_events():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    params = {
        "country": "US",  # فقط الأحداث الأمريكية
        "impact": "2,3",  # التأثير المتوسط (2) والعالي (3)
        "from_date": today.strftime('%Y-%m-%d'),
        "to_date": tomorrow.strftime('%Y-%m-%d'),
        "lang": "ar",  # اللغة العربية
    }
    
    response = requests.get(ECONOMY_API_URL, headers=HEADERS, params=params)
    events = response.json().get("events", [])
    
    return events

# نشر الأحداث على القناة
def post_events():
    events = get_economic_events()
    if events:
        message = "أحداث اقتصادية هامة للغد:\n\n"
        for event in events:
            event_time = datetime.strptime(event['time'], "%Y-%m-%d %H:%M:%S")
            time_to_event = event_time - datetime.now()

            if time_to_event > timedelta(minutes=15):  # نشر الحدث قبل 15 دقيقة من بدايته
                message += f"• {event['title']} في الساعة {event_time.strftime('%H:%M')} بتوقيت الولايات المتحدة\n"

        if message != "أحداث اقتصادية هامة للغد:\n\n":
            bot.send_message(CHANNEL_ID, message)
    else:
        bot.send_message(CHANNEL_ID, "لا توجد أحداث اقتصادية هامة للغد.")

# وظيفة بدء البوت
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "البوت بدأ بالعمل... سوف يتم نشر الأحداث الاقتصادية قريبًا.")

# وظيفة تحديث أحداث التقويم يوميًا
def schedule_daily_post():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:  # كل يوم في منتصف الليل
            post_events()
        time.sleep(60)  # تحقق كل دقيقة

# تشغيل البوت
if __name__ == '__main__':
    bot.send_message(CHANNEL_ID, "البوت بدأ بالعمل.")
    schedule_daily_post()
