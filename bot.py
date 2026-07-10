import telebot
import requests
import re
import time
import os
import json

BOT_TOKEN = "8885770583:AAEQSJh2cjHl0oPCq8Xhplx0YawzqDFR3Ok"
bot = telebot.TeleBot(BOT_TOKEN)

API1_URL = "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}"

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

def format_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    lines = ["🔥 *GET YOUR DETAILS BOYYY BY KUSHZNDR* 🔥"]
    lines.append("═" * 35)
    
    if isinstance(data, dict) and 'data' in data:
        records = data['data']
        if isinstance(records, list):
            for idx, record in enumerate(records, 1):
                lines.append(f"\n📌 *Record #{idx}*")
                lines.append("─" * 25)
                
                field_map = {
                    'mobile': '📱 Mobile',
                    'name': '👤 Name',
                    'fname': '👨 Father\'s Name',
                    'address': '📍 Address',
                    'email': '✉️ Email',
                    'id': '🆔 ID'
                }
                
                for key, label in field_map.items():
                    value = record.get(key)
                    if value and value != "None" and value != "":
                        if key == 'address':
                            value = value.replace('!', ' ').replace('  ', ' ').strip()
                            value = value.title()
                        lines.append(f"{label}: `{value}`")
                
                if record.get('address'):
                    addr_clean = record['address'].replace('!', ' ').replace('  ', ' ').strip()
                    addr_clean = addr_clean.replace(' ', '+')
                    lines.append(f"🗺️ *Map*: [Click Here](https://maps.google.com/?q={addr_clean})")
        
        if data.get('found'):
            lines.append("\n" + "═" * 35)
            lines.append(f"📊 *Total Records Found:* `{data['found']}`")
    else:
        for k, v in data.items():
            if v and v != "None" and v != "":
                lines.append(f"*{k}*: `{v}`")
    
    return "\n".join(lines)

def export_result(data, number):
    filename = f"osint_{number}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"🔥 OSINT Report for {number}\n")
        f.write("═" * 40 + "\n")
        if isinstance(data, dict) and 'data' in data:
            for idx, record in enumerate(data['data'], 1):
                f.write(f"\n📌 Record #{idx}\n")
                f.write("─" * 25 + "\n")
                for k, v in record.items():
                    if v and v != "None":
                        if k == 'address':
                            v = v.replace('!', ' ').replace('  ', ' ').strip()
                        f.write(f"{k}: {v}\n")
        else:
            f.write(str(data))
    return filename

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 
                     "🔥 *GET YOUR DETAILS BOYYY KUSHZNDR* 🔥\n\nSend any 10-digit number (without +91).\n\nExample: `9876543210`",
                     parse_mode='Markdown')

@bot.message_handler(func=lambda msg: True)
def handle_number(msg):
    chat_id = msg.chat.id
    raw = msg.text.strip()
    
    if ',' in raw or ' ' in raw:
        numbers = [clean_number(x) for x in re.split(r'[, ]+', raw) if clean_number(x)]
        if len(numbers) > 10:
            bot.reply_to(msg, "⚠️ Max 10 numbers ek saath.")
            return
        
        bot.send_message(chat_id, f"⏳ Fetching {len(numbers)} numbers...")
        for num in numbers[:10]:
            data = fetch_api1(num)
            result = format_result(data)
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    number = clean_number(raw)
    if len(number) != 10:
        bot.reply_to(msg, "❌ Invalid. Send exactly 10 digits (no +91).\nExample: `9876543210`", parse_mode='Markdown')
        return
    
    bot.send_message(chat_id, f"⏳ Fetching for `{number}`...", parse_mode='Markdown')
    
    data = fetch_api1(number)
    result = format_result(data)
    
    if len(result) > 4096:
        for i in range(0, len(result), 4096):
            bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
    
    if data and "error" not in data and data.get('data'):
        filename = export_result(data, number)
        with open(filename, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"📄 *Report for {number}*", parse_mode='Markdown')
        os.remove(filename)

if __name__ == "__main__":
    print("🔥 KUSHZNDR 🔥")  # <--- YAHAN CHANGE
    print(f"✅ Token: {BOT_TOKEN[:10]}...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)
