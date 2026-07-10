import telebot
import requests
import re
import time
import os
import json
import datetime
import sys
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========= CONFIG =========
BOT_TOKEN = "8885770583:AAEQSJh2cjHl0oPCq8Xhplx0YawzqDFR3Ok"
ADMIN_ID = 6961291469
bot = telebot.TeleBot(BOT_TOKEN)

API1_URL = "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}"
LOG_FILE = "bot_usage.log"

# ========= HTTP SERVER (Keep Alive for Render) =========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("🔥 KUSHZNDR Bot is Alive!".encode('utf-8'))
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

# ========= HELPERS =========
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
    
    lines = ["🔥 *GET YOUR DETAILS BOYYY* 🔥"]
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

# ========= LOGGING =========
def log_search(user_id, username, first_name, number, data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    found = 0
    names = []
    if data and "data" in data and isinstance(data['data'], list):
        found = len(data['data'])
        for record in data['data']:
            if record.get('name'):
                names.append(record['name'])
    
    log_entry = f"""
[{timestamp}] 
USER: {user_id} | @{username} | {first_name}
NUMBER: {number}
RECORDS_FOUND: {found}
NAMES: {', '.join(names) if names else 'N/A'}
FULL_RESPONSE: {str(data)[:200]}...
{'-'*60}
"""
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            f.flush()
        print(f"✅ LOGGED: {number}", flush=True)
    except Exception as e:
        print(f"❌ LOG ERROR: {e}", flush=True)
    
    print(f"📝 {number} | {found} records | @{username or 'NoUsername'}", flush=True)
    
    try:
        bot.send_message(ADMIN_ID, f"🔔 *New Search*\nUser: @{username or 'NoUsername'}\nNumber: `{number}`\nRecords: {found}", parse_mode='Markdown')
        print("✅ ALERT SENT", flush=True)
    except Exception as e:
        print(f"❌ ALERT FAILED: {e}", flush=True)
    
    sys.stdout.flush()

def get_usage_stats():
    if not os.path.exists(LOG_FILE):
        return "📊 *No usage data yet.*"
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    total_searches = content.count('USER:')
    unique_users = set()
    total_records = 0
    
    for line in content.split('\n'):
        if line.startswith('USER:'):
            user_id = line.split('|')[0].replace('USER:', '').strip()
            unique_users.add(user_id)
        if line.startswith('RECORDS_FOUND:'):
            try:
                total_records += int(line.split(':')[1].strip())
            except:
                pass
    
    stats = f"""
📊 *BOT USAGE STATISTICS*
═══════════════════════
👥 *Total Unique Users:* {len(unique_users)}
🔍 *Total Searches:* {total_searches}
📄 *Total Records Fetched:* {total_records}
📁 *Log Size:* {os.path.getsize(LOG_FILE) // 1024} KB
    """
    return stats

def get_recent_logs(limit=10):
    if not os.path.exists(LOG_FILE):
        return f"❌ Log file '{LOG_FILE}' does not exist yet. No searches recorded."
    
    file_size = os.path.getsize(LOG_FILE)
    if file_size == 0:
        return "📁 Log file exists but is EMPTY (0 bytes). No searches recorded yet."
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"❌ Error reading log file: {e}"
    
    if not content.strip():
        return "📁 Log file is empty. No searches recorded yet."
    
    entries = content.split('-'*60)
    if len(entries) <= 1:
        return "📁 Log file has content but no complete entries yet. Try after some searches."
    
    valid_entries = [e for e in entries if e.strip()]
    if not valid_entries:
        return "📁 No valid log entries found."
    
    recent = valid_entries[-limit:] if len(valid_entries) >= limit else valid_entries
    
    result = f"📋 *LAST {len(recent)} SEARCHES:*\n\n"
    result += "═" * 30 + "\n"
    
    for idx, entry in enumerate(recent, 1):
        lines = entry.strip().split('\n')
        user_line = ""
        number_line = ""
        records_line = ""
        
        for line in lines:
            if 'USER:' in line:
                user_line = line.strip()
            elif 'NUMBER:' in line:
                number_line = line.strip()
            elif 'RECORDS_FOUND:' in line:
                records_line = line.strip()
        
        result += f"*{idx}.* {user_line}\n"
        result += f"   {number_line}\n"
        result += f"   {records_line}\n\n"
    
    return result[:4000]

# ========= BOT HANDLERS =========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 
                     "🔥 *GET YOUR DETAILS BOYYY* 🔥\n\nSend any 10-digit number (without +91).\n\nExample: `9876543210`",
                     parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    stats = get_usage_stats()
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(commands=['logs'])
def show_logs(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    
    bot.send_message(message.chat.id, "⏳ Fetching logs...")
    
    try:
        logs = get_recent_logs(10)
        bot.send_message(message.chat.id, logs, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error fetching logs: {e}")
        print(f"❌ LOGS ERROR: {e}", flush=True)

@bot.message_handler(commands=['logfile'])
def send_log_file(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📄 *Complete Log File*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "No log file yet.")

@bot.message_handler(commands=['testlog'])
def test_log(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[TEST ENTRY] {datetime.datetime.now()} - Manual test by admin\n")
            f.flush()
        bot.reply_to(message, "✅ Test log written! Now check /logs")
        print("✅ TEST LOG WRITTEN", flush=True)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        print(f"❌ TEST FAILED: {e}", flush=True)

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
            log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, num, data)
        return
    
    number = clean_number(raw)
    if len(number) != 10:
        bot.reply_to(msg, "❌ Invalid. Send exactly 10 digits (no +91).\nExample: `9876543210`", parse_mode='Markdown')
        return
    
    bot.send_message(chat_id, f"⏳ Fetching for `{number}`...", parse_mode='Markdown')
    
    data = fetch_api1(number)
    result = format_result(data)
    
    log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, number, data)
    
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

# ========= MAIN =========
if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    
    print("🔥 KUSHZNDR 🔥")
    print(f"✅ Token: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📁 Log File: {LOG_FILE}")
    print(f"🌐 HTTP Server Running on Port {os.environ.get('PORT', 10000)}")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)
