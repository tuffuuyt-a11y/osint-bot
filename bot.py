import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import os
import json

BOT_TOKEN = "8885770583:AAEQSJh2cjHl0oPCq8Xhplx0YawzqDFR3Ok"
bot = telebot.TeleBot(BOT_TOKEN)

API1_URL = "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}"
API2_URL = "https://number2info-noobster.com-dashbord63hh7qe4.workers.dev/?key=@noob11001&mobile={}"

user_state = {}

def clean_number(raw):
    cleaned = re.sub(r'[^\d]', '', raw)
    if cleaned.startswith('91') and len(cleaned) > 10:
        cleaned = cleaned[-10:]
    return cleaned[-10:]

def fetch_api1(number):
    url = API1_URL.format(number)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_api2(number):
    url = API2_URL.format(number)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_result(data, api_name):
    if not data or "error" in data:
        return f"❌ {api_name} Error: {data.get('error', 'Unknown')}"
    lines = [f"📡 *{api_name} Results:*"]
    if isinstance(data, dict):
        for k, v in data.items():
            if v is None or v == "" or v == []:
                continue
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v[:5])
            elif isinstance(v, dict):
                v = json.dumps(v, ensure_ascii=False)[:200]
            lines.append(f"*{k}*: `{v}`")
    elif isinstance(data, list):
        for idx, item in enumerate(data[:10]):
            lines.append(f"*{idx+1}.* `{item}`")
    else:
        lines.append(f"`{data}`")
    return "\n".join(lines)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🔍 API 1 (HF)", callback_data="api1")
    btn2 = InlineKeyboardButton("🔍 API 2 (Workers)", callback_data="api2")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, 
                     "🤖 *OSINT Number Bot*\nChoose API to search:",
                     reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['api1', 'api2'])
def choose_api(call):
    chat_id = call.message.chat.id
    user_state[chat_id] = {'api': call.data}
    bot.edit_message_text(f"✅ Selected {call.data.upper()}\nNow send number (without +91):",
                          chat_id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda msg: True)
def handle_number(msg):
    chat_id = msg.chat.id
    if chat_id not in user_state:
        bot.reply_to(msg, "⚠️ First use /start to select API.")
        return
    raw = msg.text.strip()
    number = clean_number(raw)
    if len(number) != 10:
        bot.reply_to(msg, "❌ Invalid number. Send exactly 10 digits (no +91).")
        return
    api_choice = user_state[chat_id].get('api', 'api1')
    bot.send_message(chat_id, f"⏳ Fetching for `{number}`...", parse_mode='Markdown')
    if api_choice == 'api1':
        data = fetch_api1(number)
        result = format_result(data, "API 1 (HF)")
    else:
        data = fetch_api2(number)
        result = format_result(data, "API 2 (Workers)")
    if len(result) > 4096:
        for i in range(0, len(result), 4096):
            bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown')
    else:
        bot.send_message(chat_id, result, parse_mode='Markdown')

if __name__ == "__main__":
    print("🔥 Sir Kanha Bot Running...")
    bot.infinity_polling()