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
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========= CONFIG =========
BOT_TOKEN = "8885770583:AAEQSJh2cjHl0oPCq8Xhplx0YawzqDFR3Ok"
ADMIN_ID = 6961291469
bot = telebot.TeleBot(BOT_TOKEN)

API1_URL = "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}"
API2_URL = "https://adhaar2info-family-noobster.com-dashbord63hh7qe4.workers.dev/?key=@noob11001&adhaar={}"

LOG_FILE = "/tmp/bot_usage.log"

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

def clean_aadhaar(raw):
    cleaned = re.sub(r'[^\d]', '', raw)
    return cleaned[:12]  # Aadhaar 12 digits

def fetch_api1(number):
    url = API1_URL.format(number)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_api2(aadhaar):
    url = API2_URL.format(aadhaar)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # Remove developer name and add KUSHZNDR
            data = remove_dev_name(data)
            return data
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def remove_dev_name(data):
    """Recursively remove 'Dev' fields and replace with KUSHZNDR"""
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k == "Dev":
                new_dict["Dev"] = "KUSHZNDR"
            else:
                new_dict[k] = remove_dev_name(v)
        return new_dict
    elif isinstance(data, list):
        return [remove_dev_name(item) for item in data]
    else:
        return data

def format_number_result(data):
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

def format_aadhaar_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    lines = ["🔥 *AADHAAR FAMILY DETAILS* 🔥"]
    lines.append("═" * 40)
    lines.append(f"🆔 *Aadhaar:* `{data.get('adhaar', 'N/A')}`")
    lines.append(f"⏰ *Timestamp:* `{data.get('timestamp', 'N/A')}`")
    lines.append("")
    
    # Aadhaar Info
    if 'data' in data and 'aadhaar_info' in data['data']:
        aadhaar_info = data['data']['aadhaar_info']
        lines.append("📋 *AADHAAR RECORDS*")
        lines.append("─" * 30)
        lines.append(f"📊 *Total Records:* `{aadhaar_info.get('total_records', 0)}`")
        lines.append("")
        
        for idx, record in enumerate(aadhaar_info.get('records', []), 1):
            lines.append(f"📌 *Record #{idx}*")
            lines.append("─" * 20)
            lines.append(f"📱 Mobile: `{record.get('mobile', 'N/A')}`")
            lines.append(f"👤 Name: `{record.get('name', 'N/A')}`")
            lines.append(f"👨 Father: `{record.get('fname', 'N/A')}`")
            lines.append(f"📧 Email: `{record.get('email', 'N/A')}`")
            lines.append(f"📞 Alternate: `{record.get('alt', 'N/A')}`")
            lines.append(f"🔄 Circle: `{record.get('circle', 'N/A')}`")
            
            # Clean address
            address = record.get('address', '')
            if address:
                address = address.replace('!', ' ').replace('  ', ' ').strip()
                lines.append(f"📍 Address: `{address}`")
            lines.append("")
    
    # Family Info
    if 'data' in data and 'family_info' in data['data']:
        family_info = data['data']['family_info']
        lines.append("👨‍👩‍👧‍👦 *FAMILY DETAILS*")
        lines.append("─" * 30)
        lines.append(f"👥 *Total Members:* `{family_info.get('total_members', 0)}`")
        lines.append("")
        
        # Ration Card
        if 'ration_card' in family_info:
            rc = family_info['ration_card']
            lines.append("📄 *Ration Card*")
            lines.append("─" * 15)
            lines.append(f"🏛️ State: `{rc.get('state_name', 'N/A')}`")
            lines.append(f"🏙️ District: `{rc.get('district_name', 'N/A')}`")
            lines.append(f"🆔 Card No: `{rc.get('ration_card_no', 'N/A')}`")
            lines.append(f"📋 Scheme: `{rc.get('scheme_name', 'N/A')}`")
            lines.append("")
        
        # Members
        if 'members' in family_info:
            lines.append("👨‍👩‍👧 *Family Members*")
            lines.append("─" * 15)
            for member in family_info['members']:
                name = member.get('member_name', 'N/A')
                mem_id = member.get('member_id', 'N/A')
                sno = member.get('s_no', 'N/A')
                lines.append(f"👤 *{sno}.* `{name}`")
                lines.append(f"   ID: `{mem_id}`")
            lines.append("")
        
        # Additional Info
        if 'additional_info' in family_info:
            ai = family_info['additional_info']
            lines.append("ℹ️ *Additional Info*")
            lines.append("─" * 15)
            lines.append(f"🔁 Duplicate Aadhaar: `{ai.get('duplicate_aadhaar_beneficiary', False)}`")
            lines.append(f"🏦 Central Repository: `{ai.get('exists_in_central_repository', False)}`")
            lines.append(f"📦 FPS Category: `{ai.get('fps_category', 'N/A')}`")
            lines.append(f"✅ IMPDS Allowed: `{ai.get('impds_transaction_allowed', False)}`")
    
    # Developer Credit
    lines.append("")
    lines.append("═" * 40)
    lines.append("🔥 *Developed by: KUSHZNDR* 🔥")
    
    return "\n".join(lines)

def export_result(data, number, query_type):
    filename = f"{query_type}_{number}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"🔥 {query_type.upper()} Report for {number}\n")
        f.write("═" * 40 + "\n")
        f.write(json.dumps(data, indent=2, ensure_ascii=False))
    return filename

# ========= LOGGING =========
def log_search(user_id, username, first_name, query_type, query_value, data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    found = 0
    if query_type == "number":
        if data and "data" in data and isinstance(data['data'], list):
            found = len(data['data'])
    elif query_type == "aadhaar":
        if data and "data" in data and "family_info" in data['data']:
            found = data['data']['family_info'].get('total_members', 0)
    
    log_entry = f"""
[{timestamp}] 
TYPE: {query_type.upper()}
USER: {user_id} | @{username} | {first_name}
QUERY: {query_value}
RECORDS_FOUND: {found}
FULL_RESPONSE: {str(data)[:200]}...
{'-'*60}
"""
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            f.flush()
        print(f"✅ LOGGED: {query_type} | {query_value}", flush=True)
    except Exception as e:
        print(f"❌ LOG ERROR: {e}", flush=True)
    
    print(f"📝 {query_type} | {query_value} | {found} records", flush=True)
    
    try:
        bot.send_message(ADMIN_ID, f"🔔 *New {query_type.upper()} Search*\nUser: @{username or 'NoUsername'}\nQuery: `{query_value}`\nRecords: {found}", parse_mode='Markdown')
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
        return f"❌ Log file does not exist yet."
    
    file_size = os.path.getsize(LOG_FILE)
    if file_size == 0:
        return "📁 Log file is EMPTY (0 bytes)."
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"❌ Error reading log file: {e}"
    
    if not content.strip():
        return "📁 Log file is empty."
    
    entries = content.split('-'*60)
    valid_entries = [e for e in entries if e.strip()]
    if not valid_entries:
        return "📁 No valid log entries found."
    
    recent = valid_entries[-limit:] if len(valid_entries) >= limit else valid_entries
    
    result = f"📋 *LAST {len(recent)} SEARCHES:*\n\n"
    result += "═" * 30 + "\n"
    
    for idx, entry in enumerate(recent, 1):
        lines = entry.strip().split('\n')
        type_line = ""
        user_line = ""
        query_line = ""
        records_line = ""
        
        for line in lines:
            if 'TYPE:' in line:
                type_line = line.strip()
            elif 'USER:' in line:
                user_line = line.strip()
            elif 'QUERY:' in line:
                query_line = line.strip()
            elif 'RECORDS_FOUND:' in line:
                records_line = line.strip()
        
        result += f"*{idx}.* {type_line}\n"
        result += f"   {user_line}\n"
        result += f"   {query_line}\n"
        result += f"   {records_line}\n\n"
    
    return result[:4000]

# ========= BOT HANDLERS =========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📱 Number to Details", callback_data="num")
    btn2 = InlineKeyboardButton("🆔 Aadhaar to Family", callback_data="aadhaar")
    markup.add(btn1, btn2)
    
    bot.send_message(chat_id, 
                     "🔥 *KUSHZNDR OSINT BOT* 🔥\n\nChoose an option:",
                     reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['num', 'aadhaar'])
def choose_option(call):
    chat_id = call.message.chat.id
    if call.data == 'num':
        bot.edit_message_text("📱 *Number to Details*\n\nSend any 10-digit number (without +91).\n\nExample: `9876543210`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        # Set user state
        user_state[chat_id] = {'mode': 'number'}
    elif call.data == 'aadhaar':
        bot.edit_message_text("🆔 *Aadhaar to Family Details*\n\nSend any 12-digit Aadhaar number.\n\nExample: `352283381852`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        user_state[chat_id] = {'mode': 'aadhaar'}

# User state dictionary
user_state = {}

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
            f.write(f"\n[TEST] {datetime.datetime.now()} - Manual test\n")
            f.flush()
        bot.reply_to(message, "✅ Test log written! Check /logs")
        print("✅ TEST LOG WRITTEN", flush=True)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        print(f"❌ TEST FAILED: {e}", flush=True)

@bot.message_handler(func=lambda msg: True)
def handle_query(msg):
    chat_id = msg.chat.id
    raw = msg.text.strip()
    
    # Check if user has selected mode
    if chat_id not in user_state:
        bot.reply_to(msg, "⚠️ First use /start to select an option.")
        return
    
    mode = user_state[chat_id].get('mode', 'number')
    
    if mode == 'number':
        # Number mode
        number = clean_number(raw)
        if len(number) != 10:
            bot.reply_to(msg, "❌ Invalid number. Send exactly 10 digits (no +91).\nExample: `9876543210`", parse_mode='Markdown')
            return
        
        bot.send_message(chat_id, f"⏳ Fetching details for `{number}`...", parse_mode='Markdown')
        
        data = fetch_api1(number)
        result = format_number_result(data)
        
        log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, "number", number, data)
        
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        
        if data and "error" not in data and data.get('data'):
            filename = export_result(data, number, "number")
            with open(filename, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📄 *Number Report for {number}*", parse_mode='Markdown')
            os.remove(filename)
    
    elif mode == 'aadhaar':
        # Aadhaar mode
        aadhaar = clean_aadhaar(raw)
        if len(aadhaar) != 12:
            bot.reply_to(msg, "❌ Invalid Aadhaar. Send exactly 12 digits.\nExample: `352283381852`", parse_mode='Markdown')
            return
        
        bot.send_message(chat_id, f"⏳ Fetching family details for Aadhaar `{aadhaar}`...", parse_mode='Markdown')
        
        data = fetch_api2(aadhaar)
        result = format_aadhaar_result(data)
        
        log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, "aadhaar", aadhaar, data)
        
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        
        if data and "error" not in data and data.get('success'):
            filename = export_result(data, aadhaar, "aadhaar")
            with open(filename, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📄 *Aadhaar Report for {aadhaar}*", parse_mode='Markdown')
            os.remove(filename)
    
    # Reset state after query
    # user_state[chat_id] = {'mode': mode}  # Keep mode for next query

# ========= MAIN =========
if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    
    print("🔥 KUSHZNDR 🔥")
    print(f"✅ Token: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📁 Log File: {LOG_FILE}")
    print(f"🌐 HTTP Server Running on Port {os.environ.get('PORT', 10000)}")
    print("⏳ Bot is starting...")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)
