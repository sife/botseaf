import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import logging
import telegram
import time

# إعدادات تيليجرام
BOT_TOKEN = '7731023681:AAHNztczvrywAK0ZDGAKC1vqdW82eG-TpUQ'
CHANNEL_ID = '@testbotseaf'

# التوقيت المحلي (مثلاً توقيت السعودية)
TIMEZONE = pytz.timezone("Asia/Riyadh")

# تهيئة البوت
bot = telegram.Bot(token=BOT_TOKEN)

# سجل الأخبار المُرسلة لتجنب التكرار
sent_news = set()

def fetch_usd_news():
    url = "https://sa.investing.com/economic-calendar/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    news_list = []

    rows = soup.select('tr.js-event-item')
    for row in rows:
        currency = row.get('data-event-currency', '')
        impact = row.get('data-impact', '')
        if currency != 'USD' or impact not in ['2', '3']:  # 2 = متوسط، 3 = قوي
            continue

        # وقت وتاريخ الحدث
        time_str = row.get('data-event-datetime', '')
        if not time_str:
            continue

        event_time_utc = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        event_time_local = event_time_utc.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)

        # عنوان الحدث
        title = row.select_one('.event').get_text(strip=True)

        # تجاهل الأحداث اللي مر وقتها
        now = datetime.now(TIMEZONE)
        if now > event_time_local:
            continue

        # إذا باقي 15 دقيقة أو أقل، نجهز الرسالة
        minutes_diff = (event_time_local - now).total_seconds() / 60
        if 0 < minutes_diff <= 15:
            news_id = f"{title}_{event_time_local.strftime('%Y%m%d%H%M')}"
            if news_id not in sent_news:
                sent_news.add(news_id)

                impact_text = "قوي 🔥" if impact == '3' else "متوسط ⚠️"
                date_str = event_time_local.strftime('%A، %d %B %Y')
                time_str = event_time_local.strftime('%H:%M')

                message = f"""📊 خبر اقتصادي قادم بعد قليل!

🔹 العملة: USD 🇺🇸  
🔹 الحدث: {title}  
📅 التاريخ: {date_str}  
⏰ الوقت: {time_str} بتوقيت مكة  
📈 التأثير المتوقع: {impact_text}

⏳ سيتم صدور الخبر خلال 15 دقيقة!
"""
                send_telegram_message(message)

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        print("✅ تم إرسال الخبر")
    except Exception as e:
        print(f"❌ خطأ أثناء الإرسال: {e}")

if __name__ == '__main__':
    print("🚀 البوت يعمل... سيتم التحقق من الأخبار كل ساعة")
    while True:
        try:
            fetch_usd_news()
        except Exception as e:
            logging.exception("حدث خطأ أثناء جلب الأخبار")

        time.sleep(3600)  # انتظار ساعة كاملة
