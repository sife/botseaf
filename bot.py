import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# بيانات البوت
TOKEN = "7712506538:AAHgFTEg7_fuhq0sTN2dwZ88UFV1iQ6ycQ4"
CHANNEL_ID = "@testbotseaf"
bot = telebot.TeleBot(TOKEN)

# رابط صفحة التقويم الاقتصادي
ECONOMY_URL = "https://ar.fxstreet.com/economic-calendar"

# جلب البيانات الاقتصادية
def get_economic_events():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    # إرسال طلب لجلب صفحة التقويم
    response = requests.get(ECONOMY_URL)
    if response.status_code != 200:
        print("Error fetching the page")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # العثور على جدول الأحداث
    events_table = soup.find_all('div', class_='calendar__event')

    events = []
    for event in events_table:
        title = event.find('span', class_='calendar__event-title').text.strip()
        date_time = event.find('span', class_='calendar__date').text.strip()
        impact = event.find('span', class_='calendar__impact').get('title', '').strip()

        # إضافة الحدث فقط إذا كان له تأثير متوسط أو عالي
        if 'متوسط' in impact or 'عالي' in impact:
            events.append({
                'title': title,
                'date_time': date_time,
                'impact': impact
            })

    return events

# نشر الأحداث على القناة
def post_events():
    events = get_economic_events()
    if events:
        message = "أحداث اقتصادية هامة للغد:\n\n"
        for event in events:
            event_time = datetime.strptime(event['date_time'], "%d %b %Y %H:%M")
            time_to_event = event_time - datetime.now()

            if time_to_event > timedelta(minutes=15):  # نشر الحدث قبل 15 دقيقة من بدايته
                message += f"• {event['title']} في الساعة {event_time.strftime('%H:%M')} بتوقيت الولايات المتحدة\n"

        if message != "أحداث اقتصادية هامة للغد:\n\n":
            bot.send_message(CHANNEL_ID, message)
        else:
            print("No events found to post.")
    else:
        print("No events to fetch.")

# وظيفة بدء البوت
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "البوت بدأ بالعمل... سوف يتم نشر الأحداث الاقتصادية قريبًا.")

# وظيفة تحديث أحداث التقويم يوميًا
def schedule_daily_post():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:  # كل يوم في منتصف الليل
            print("Posting events for the day.")
            post_events()
        time.sleep(60)  # تحقق كل دقيقة

# تشغيل البوت
if __name__ == '__main__':
    bot.send_message(CHANNEL_ID, "البوت بدأ بالعمل.")
    schedule_daily_post()
