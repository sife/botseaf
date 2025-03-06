import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
import requests
from alpha_vantage.foreignexchange import ForeignExchange

# إعدادات البوت
TOKEN = "8199102034:AAFcguhaf_J36XgM4avtO--pppKBZvEyX38"
ALPHA_VANTAGE_API_KEY = "QOHNYLST38AYFCLD"
NEWSAPI_API_KEY = "9707513d693d4eaeafd3e13b70b322ae"

openai.api_key = "YOUR_OPENAI_API_KEY"

# تهيئة تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> None:
    """الرد عند بدء المحادثة مع البوت"""
    keyboard = [[InlineKeyboardButton("📊 تحليل الأسواق", callback_data='market_analysis')],
                [InlineKeyboardButton("📉 توصيات التداول", callback_data='trading_signals')],
                [InlineKeyboardButton("📢 آخر الأخبار الاقتصادية", callback_data='latest_news')],
                [InlineKeyboardButton("🔔 تنبيهات الأسعار", callback_data='price_alerts')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("مرحبًا بك في SA Forex AI! كيف يمكنني مساعدتك؟", reply_markup=reply_markup)

def get_openai_response(text):
    """إرسال استفسارات إلى ChatGPT"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "أنت مساعد خبير في التداول."},
                  {"role": "user", "content": text}]
    )
    return response['choices'][0]['message']['content']

def handle_message(update: Update, context: CallbackContext) -> None:
    """الرد على استفسارات المستخدم"""
    user_message = update.message.text
    response = get_openai_response(user_message)
    update.message.reply_text(response)

def fetch_market_news():
    """جلب آخر الأخبار الاقتصادية"""
    url = f"https://newsapi.org/v2/everything?q=forex&language=ar&apiKey={NEWSAPI_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        if articles:
            return {"headline": articles[0]["title"], "summary": articles[0]["description"]}
    return {"error": "تعذر جلب الأخبار"}

def market_news(update: Update, context: CallbackContext) -> None:
    """إرسال آخر الأخبار المالية"""
    news = fetch_market_news()
    if "error" in news:
        update.message.reply_text(news["error"])
    else:
        update.message.reply_text(f"📰 آخر الأخبار: {news['headline']}\n{news['summary']}")

def fetch_market_data(symbol):
    """جلب بيانات السوق باستخدام Alpha Vantage"""
    fx = ForeignExchange(key=ALPHA_VANTAGE_API_KEY)
    data, _ = fx.get_currency_exchange_rate(from_currency=symbol[:3], to_currency=symbol[3:])
    if "5. Exchange Rate" in data:
        return {"price": float(data["5. Exchange Rate"]), "trend": "غير متاح"}
    return {"error": "تعذر جلب بيانات السوق"}

def market_analysis(update: Update, context: CallbackContext) -> None:
    """تحليل الأسواق المالية"""
    symbol = "EURUSD"  # يمكن تغييره لاحقًا لجعله ديناميكيًا
    data = fetch_market_data(symbol)
    if "error" in data:
        update.message.reply_text(data["error"])
    else:
        update.message.reply_text(f"📊 تحليل {symbol}:\nالسعر الحالي: {data['price']}\nاتجاه السوق: {data['trend']}")

def price_alert(update: Update, context: CallbackContext) -> None:
    """إعداد تنبيهات الأسعار"""
    update.message.reply_text("🔔 قم بإرسال السعر المستهدف مع رمز العملة (مثلاً: 1.2000 EURUSD)")
    # هنا يمكن إضافة منطق لتخزين التنبيهات وتنفيذها لاحقًا

def main():
    """تشغيل البوت"""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler("news", market_news))
    dp.add_handler(CommandHandler("analysis", market_analysis))
    dp.add_handler(CommandHandler("alert", price_alert))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
