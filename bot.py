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

# ========= 5 NUMBER APIs =========
API_LIST = [
    {
        "name": "API1",
        "url": "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}",
        "type": "query_param"
    },
    {
        "name": "API2",
        "url": "https://number2info-noobster.com-dashbord63hh7qe4.workers.dev/?key=@noob11001&mobile={}",
        "type": "query_param"
    },
    {
        "name": "API3",
        "url": "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}",
        "type": "query_param"
    },
    {
        "name": "API4",
        "url": "https://tfqdeadlo-inddataapi.hf.space/search?mobile={}",
        "type": "query_param"
    },
    {
        "name": "API5",
        "url": "https://tfqdeadlo-850crfastsearch.hf.space/search/{}",
        "type": "path_param"
    }
]

# Other APIs (Aadhaar, GST, Vehicle - same as before)
API3_URL = "https://adhaar2info-family-noobster.com-dashbord63hh7qe4.workers.dev/?key=@noob11001&adhaar={}"
API4_URL = "https://gst-pan-api.onrender.com/gstin-detail/{}"
API5_URL = "https://vvvin-ng.vercel.app/lookup?rc={}"

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
    return cleaned[:12]

def clean_gst(raw):
    cleaned = re.sub(r'[^A-Za-z0-9]', '', raw)
    return cleaned.upper()[:15]

def clean_vehicle(raw):
    cleaned = re.sub(r'[^A-Za-z0-9]', '', raw)
    return cleaned.upper()

# ========= FETCH FUNCTIONS =========
def fetch_single_api(api_config, number):
    """Fetch data from a single API"""
    try:
        if api_config["type"] == "query_param":
            url = api_config["url"].format(number)
        else:  # path_param
            url = api_config["url"].format(number)
        
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            # Check if API returned valid data
            if data and "error" not in data:
                # For API5 specific format
                if api_config["name"] == "API5" and data.get("status") == "success":
                    return {"success": True, "data": data.get("data"), "source": api_config["name"]}
                # For other APIs with 'data' field
                elif "data" in data and data["data"]:
                    return {"success": True, "data": data["data"], "source": api_config["name"]}
                # For APIs with direct subscriber data
                elif "subscriber" in data:
                    return {"success": True, "data": data["subscriber"], "source": api_config["name"]}
        return {"success": False, "data": None, "source": api_config["name"]}
    except Exception as e:
        print(f"⚠️ {api_config['name']} failed: {e}", flush=True)
        return {"success": False, "data": None, "source": api_config["name"]}

def fetch_all_apis(number):
    """Fetch from all number APIs and pick the best result"""
    results = []
    
    for api in API_LIST:
        result = fetch_single_api(api, number)
        if result["success"] and result["data"]:
            results.append(result)
    
    if not results:
        return {"error": "No data found", "data": []}
    
    # Pick the API with most data fields
    best_result = max(results, key=lambda x: len(x["data"]) if isinstance(x["data"], dict) else 0)
    
    # Format data for consistency
    if isinstance(best_result["data"], dict):
        # Convert to list format for display
        formatted_data = [best_result["data"]]
    else:
        formatted_data = best_result["data"] if isinstance(best_result["data"], list) else []
    
    return {
        "success": True,
        "data": formatted_data,
        "source": best_result["source"],
        "found": len(formatted_data)
    }

def fetch_api2(aadhaar):
    url = API3_URL.format(aadhaar)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            data = remove_dev_name(data)
            return data
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_api3(gst):
    url = API4_URL.format(gst)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if 'credit' in data:
                del data['credit']
            return data
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_api4(vehicle):
    url = API5_URL.format(vehicle)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def remove_dev_name(data):
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

# ========= FORMATTERS =========
def format_number_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    # Check if any data found
    if not data.get('data') or len(data['data']) == 0:
        return """
😔 *Sorry, we can't find data from your input.*
📭 *It's not in our database.*

💡 *Try:*
• Double-check the number (10 digits, no +91)
• Try another number
• Make sure the number is active

🔥 *Powered by KUSHZNDR* 🔥
"""
    
    lines = ["🔥 *ADVANCED NUMBER DETAILS* 🔥"]
    lines.append("═" * 40)
    
    if data.get('source'):
        lines.append(f"📡 *Source:* `{data['source']}`")
        lines.append(f"📊 *Total Records:* `{data.get('found', 0)}`")
        lines.append("")
    
    for idx, record in enumerate(data['data'], 1):
        lines.append(f"📌 *Record #{idx}*")
        lines.append("─" * 30)
        
        field_map = {
            'mobile': '📱 Mobile',
            'name': '👤 Name',
            'fname': '👨 Father\'s Name',
            'address': '📍 Address',
            'email': '✉️ Email',
            'carrier': '📶 Carrier',
            'circle': '🔄 Circle',
            'alt': '📞 Alternate',
            'id': '🆔 ID',
            'fps_category': '📦 FPS Category',
            'status': '📊 Status',
            'registration_date': '📅 Registration Date'
        }
        
        for key, label in field_map.items():
            value = record.get(key)
            if value and value != "None" and value != "" and value != "N/A":
                if key == 'address':
                    value = value.replace('!', ' ').replace('  ', ' ').strip()
                    value = value.title()
                lines.append(f"{label}: `{value}`")
        
        if record.get('address'):
            addr_clean = record['address'].replace('!', ' ').replace('  ', ' ').strip()
            addr_clean = addr_clean.replace(' ', '+')
            lines.append(f"🗺️ *Map*: [Click Here](https://maps.google.com/?q={addr_clean})")
        
        lines.append("")
    
    lines.append("═" * 40)
    lines.append(f"📡 *Data fetched from: {data.get('source', 'Unknown')}*")
    lines.append("")
    lines.append("═" * 40)
    lines.append("🔥 *Powered by KUSHZNDR* 🔥")
    
    return "\n".join(lines)

def format_aadhaar_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    if not data.get('data') or not data['data'].get('aadhaar_info'):
        return """
😔 *Sorry, we can't find data from your input.*
📭 *It's not in our database.*

💡 *Try:*
• Double-check the Aadhaar number (12 digits)
• Try another Aadhaar number
• Make sure the number is valid

🔥 *Powered by KUSHZNDR* 🔥
"""
    
    lines = ["🔥 *AADHAAR FAMILY DETAILS* 🔥"]
    lines.append("═" * 40)
    lines.append(f"🆔 *Aadhaar:* `{data.get('adhaar', 'N/A')}`")
    lines.append(f"⏰ *Timestamp:* `{data.get('timestamp', 'N/A')}`")
    lines.append("")
    
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
            
            address = record.get('address', '')
            if address:
                address = address.replace('!', ' ').replace('  ', ' ').strip()
                lines.append(f"📍 Address: `{address}`")
            lines.append("")
    
    if 'data' in data and 'family_info' in data['data']:
        family_info = data['data']['family_info']
        lines.append("👨‍👩‍👧‍👦 *FAMILY DETAILS*")
        lines.append("─" * 30)
        lines.append(f"👥 *Total Members:* `{family_info.get('total_members', 0)}`")
        lines.append("")
        
        if 'ration_card' in family_info and family_info['ration_card'] is not None:
            rc = family_info['ration_card']
            lines.append("📄 *Ration Card*")
            lines.append("─" * 15)
            lines.append(f"🏛️ State: `{rc.get('state_name', 'N/A')}`")
            lines.append(f"🏙️ District: `{rc.get('district_name', 'N/A')}`")
            lines.append(f"🆔 Card No: `{rc.get('ration_card_no', 'N/A')}`")
            lines.append(f"📋 Scheme: `{rc.get('scheme_name', 'N/A')}`")
            lines.append("")
        else:
            lines.append("📄 *Ration Card:* `Not Available`")
            lines.append("")
        
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
        else:
            lines.append("👨‍👩‍👧 *Family Members:* `Not Available`")
            lines.append("")
        
        if 'additional_info' in family_info and family_info['additional_info'] is not None:
            ai = family_info['additional_info']
            lines.append("ℹ️ *Additional Info*")
            lines.append("─" * 15)
            lines.append(f"🔁 Duplicate Aadhaar: `{ai.get('duplicate_aadhaar_beneficiary', False)}`")
            lines.append(f"🏦 Central Repository: `{ai.get('exists_in_central_repository', False)}`")
            lines.append(f"📦 FPS Category: `{ai.get('fps_category', 'N/A')}`")
            lines.append(f"✅ IMPDS Allowed: `{ai.get('impds_transaction_allowed', False)}`")
    
    lines.append("")
    lines.append("═" * 40)
    lines.append("🔥 *Powered by KUSHZNDR* 🔥")
    
    return "\n".join(lines)

def format_gst_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    if not data.get('gstin') or not data.get('razorpay_info'):
        return """
😔 *Sorry, we can't find data from your input.*
📭 *It's not in our database.*

💡 *Try:*
• Double-check the GST number (15 characters)
• Try another GST number
• Make sure the number is valid

🔥 *Powered by KUSHZNDR* 🔥
"""
    
    lines = ["🔥 *GST COMPANY DETAILS* 🔥"]
    lines.append("═" * 40)
    lines.append("🔥 *Developed by: KUSHZNDR* 🔥")
    lines.append("")
    
    if data.get('gstin'):
        lines.append(f"🆔 *GSTIN:* `{data.get('gstin')}`")
    
    if 'razorpay_info' in data:
        razorpay = data['razorpay_info']
        if 'enrichment_details' in razorpay:
            enrichment = razorpay['enrichment_details']
            if 'online_provider' in enrichment:
                provider = enrichment['online_provider']
                if 'details' in provider:
                    details = provider['details']
                    lines.append("")
                    lines.append("📋 *COMPANY DETAILS*")
                    lines.append("─" * 30)
                    
                    field_map = {
                        'legal_name': '🏢 Legal Name',
                        'trade_name': '📛 Trade Name',
                        'gstin': '🆔 GSTIN',
                        'constitution': '📋 Constitution',
                        'tax_payer_type': '💰 Taxpayer Type',
                        'status': '📊 Status',
                        'registration_date': '📅 Registration Date',
                        'state_jurisdiction': '🏛️ State Jurisdiction',
                        'central_jurisdiction': '🏛️ Central Jurisdiction',
                        'primary_address': '📍 Primary Address'
                    }
                    
                    for key, label in field_map.items():
                        value = details.get(key)
                        if value and value != "":
                            lines.append(f"{label}: `{value}`")
    
    lines.append("")
    lines.append("═" * 40)
    lines.append("🔥 *Powered by KUSHZNDR* 🔥")
    
    return "\n".join(lines)

def format_vehicle_result(data):
    if not data or "error" in data:
        return f"❌ *Error:* {data.get('error', 'Unknown')}"
    
    if not data.get('registration_number'):
        return """
😔 *Sorry, we can't find data from your input.*
📭 *It's not in our database.*

💡 *Try:*
• Double-check the registration number (e.g., MH12DE1433)
• Try another vehicle number
• Make sure the number is valid

🔥 *Powered by KUSHZNDR* 🔥
"""
    
    lines = ["🚗 *VEHICLE DETAILS* 🔥"]
    lines.append("═" * 40)
    
    if data.get('registration_number'):
        lines.append(f"🔢 *Registration No:* `{data.get('registration_number')}`")
    
    if 'Ownership Details' in data:
        own = data['Ownership Details']
        lines.append("")
        lines.append("👤 *OWNERSHIP DETAILS*")
        lines.append("─" * 25)
        
        owner_name = own.get('Owner Name', 'N/A')
        father_name = own.get("Father's Name", 'N/A')
        serial_no = own.get('Owner Serial No', 'N/A')
        rto = own.get('Registered RTO', 'N/A')
        
        lines.append(f"👤 Owner: `{owner_name}`")
        lines.append(f"👨 Father: `{father_name}`")
        lines.append(f"📋 Serial No: `{serial_no}`")
        lines.append(f"🏛️ RTO: `{rto}`")
    
    if 'Vehicle Details' in data:
        veh = data['Vehicle Details']
        lines.append("")
        lines.append("🚘 *VEHICLE DETAILS*")
        lines.append("─" * 25)
        lines.append(f"🚙 Model: `{veh.get('Model Name', 'N/A')}`")
        lines.append(f"🔧 Maker: `{veh.get('Maker Model', 'N/A')}`")
        lines.append(f"📋 Class: `{veh.get('Vehicle Class', 'N/A')}`")
        lines.append(f"⛽ Fuel: `{veh.get('Fuel Type', 'N/A')}`")
        lines.append(f"🔩 Chassis: `{veh.get('Chassis Number', 'N/A')}`")
        lines.append(f"⚙️ Engine: `{veh.get('Engine Number', 'N/A')}`")
    
    if 'Insurance Information' in data:
        ins = data['Insurance Information']
        lines.append("")
        lines.append("🛡️ *INSURANCE DETAILS*")
        lines.append("─" * 25)
        lines.append(f"📅 Expiry: `{ins.get('Insurance Expiry', 'N/A')}`")
        lines.append(f"📄 Policy No: `{ins.get('Insurance No', 'N/A')}`")
        lines.append(f"🏢 Company: `{ins.get('Insurance Company', 'N/A')}`")
    
    if 'Important Dates & Validity' in data:
        dates = data['Important Dates & Validity']
        lines.append("")
        lines.append("📅 *IMPORTANT DATES*")
        lines.append("─" * 25)
        lines.append(f"📆 Registration: `{dates.get('Registration Date', 'N/A')}`")
        lines.append(f"⏳ Age: `{dates.get('Vehicle Age', 'N/A')}`")
        lines.append(f"✅ Fitness Upto: `{dates.get('Fitness Upto', 'N/A')}`")
        lines.append(f"💰 Tax Upto: `{dates.get('Tax Upto', 'N/A')}`")
        lines.append(f"📋 PUC Upto: `{dates.get('PUC Upto', 'N/A')}`")
        lines.append(f"🛡️ Insurance Upto: `{dates.get('Insurance Upto', 'N/A')}`")
    
    if 'Other Information' in data:
        other = data['Other Information']
        financer = other.get('Financer Name', 'N/A')
        if financer and financer != 'NA':
            lines.append("")
            lines.append("ℹ️ *OTHER INFO*")
            lines.append("─" * 25)
            lines.append(f"🏦 Financer: `{financer}`")
            lines.append(f"📦 Capacity: `{other.get('Cubic Capacity', 'N/A')}`")
            lines.append(f"💺 Seating: `{other.get('Seating Capacity', 'N/A')}`")
    
    if 'Basic Card Info' in data:
        basic = data['Basic Card Info']
        lines.append("")
        lines.append("📍 *RTO CONTACT*")
        lines.append("─" * 25)
        lines.append(f"🏛️ RTO: `{basic.get('City Name', 'N/A')} ({basic.get('Code', 'N/A')})`")
        lines.append(f"📞 Phone: `{basic.get('Phone', 'N/A')}`")
        lines.append(f"🌐 Website: `{basic.get('Website', 'N/A')}`")
        lines.append(f"📍 Address: `{basic.get('Address', 'N/A')}`")
    
    lines.append("")
    lines.append("═" * 40)
    lines.append("🔥 *Powered by KUSHZNDR* 🔥")
    
    return "\n".join(lines)

def export_result(data, query, query_type):
    filename = f"{query_type}_{query}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"🔥 {query_type.upper()} Report for {query}\n")
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
    elif query_type == "gst":
        if data and "gstin" in data:
            found = 1
    elif query_type == "vehicle":
        if data and "registration_number" in data:
            found = 1
    
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
        return "❌ Log file does not exist yet."
    
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
    
    result = "📋 LAST " + str(len(recent)) + " SEARCHES:\n\n"
    result += "=" * 30 + "\n"
    
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
        
        result += str(idx) + ". " + type_line + "\n"
        result += "   " + user_line + "\n"
        result += "   " + query_line + "\n"
        result += "   " + records_line + "\n\n"
    
    return result[:4000]

# ========= BOT HANDLERS =========
user_state = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📱 Number", callback_data="num")
    btn2 = InlineKeyboardButton("🆔 Aadhaar", callback_data="aadhaar")
    btn3 = InlineKeyboardButton("🏢 GST", callback_data="gst")
    btn4 = InlineKeyboardButton("🚗 Vehicle", callback_data="vehicle")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(chat_id, 
                     "🔥 *KUSHZNDR OSINT BOT* 🔥\n\nChoose an option:",
                     reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['num', 'aadhaar', 'gst', 'vehicle'])
def choose_option(call):
    chat_id = call.message.chat.id
    if call.data == 'num':
        bot.edit_message_text("📱 *Number to Details*\n\nSend any 10-digit number (without +91).\n\nExample: `9876543210`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        user_state[chat_id] = {'mode': 'number'}
    elif call.data == 'aadhaar':
        bot.edit_message_text("🆔 *Aadhaar to Family Details*\n\nSend any 12-digit Aadhaar number.\n\nExample: `352283381852`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        user_state[chat_id] = {'mode': 'aadhaar'}
    elif call.data == 'gst':
        bot.edit_message_text("🏢 *GST to Company Details*\n\nSend any 15-character GST number.\n\nExample: `07AABCF8078M1Z3`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        user_state[chat_id] = {'mode': 'gst'}
    elif call.data == 'vehicle':
        bot.edit_message_text("🚗 *Vehicle to Details*\n\nSend your vehicle registration number.\n\nExample: `MH12DE1433`",
                              chat_id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        user_state[chat_id] = {'mode': 'vehicle'}

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
        bot.send_message(message.chat.id, logs, parse_mode=None)
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
    
    if chat_id not in user_state:
        bot.reply_to(msg, "⚠️ First use /start to select an option.")
        return
    
    mode = user_state[chat_id].get('mode', 'number')
    
    if mode == 'number':
        number = clean_number(raw)
        if len(number) != 10:
            bot.reply_to(msg, "❌ Invalid number. Send exactly 10 digits (no +91).\nExample: `9876543210`", parse_mode='Markdown')
            return
        
        # ===== WAITING MESSAGE =====
        waiting_msg = bot.send_message(chat_id, "⏳ *This might take a few seconds... Kindly wait while we fetch the best data from multiple sources.*", parse_mode='Markdown')
        
        data = fetch_all_apis(number)
        result = format_number_result(data)
        
        # Delete waiting message
        try:
            bot.delete_message(chat_id, waiting_msg.message_id)
        except:
            pass
        
        log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, "number", number, data)
        
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        
        if data and "error" not in data and data.get('data'):
            filename = export_result(data, number, "number")
            with open(filename, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📄 *Merged Report for {number}*", parse_mode='Markdown')
            os.remove(filename)
    
    elif mode == 'aadhaar':
        aadhaar = clean_aadhaar(raw)
        if len(aadhaar) != 12:
            bot.reply_to(msg, "❌ Invalid Aadhaar. Send exactly 12 digits.\nExample: `352283381852`", parse_mode='Markdown')
            return
        
        waiting_msg = bot.send_message(chat_id, "⏳ *This might take a few seconds... Kindly wait.*", parse_mode='Markdown')
        
        data = fetch_api2(aadhaar)
        result = format_aadhaar_result(data)
        
        try:
            bot.delete_message(chat_id, waiting_msg.message_id)
        except:
            pass
        
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
    
    elif mode == 'gst':
        gst = clean_gst(raw)
        if len(gst) != 15:
            bot.reply_to(msg, "❌ Invalid GST. Send exactly 15 characters.\nExample: `07AABCF8078M1Z3`", parse_mode='Markdown')
            return
        
        waiting_msg = bot.send_message(chat_id, "⏳ *This might take a few seconds... Kindly wait.*", parse_mode='Markdown')
        
        data = fetch_api3(gst)
        result = format_gst_result(data)
        
        try:
            bot.delete_message(chat_id, waiting_msg.message_id)
        except:
            pass
        
        log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, "gst", gst, data)
        
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        
        if data and "error" not in data and data.get('gstin'):
            filename = export_result(data, gst, "gst")
            with open(filename, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📄 *GST Report for {gst}*", parse_mode='Markdown')
            os.remove(filename)
    
    elif mode == 'vehicle':
        vehicle = clean_vehicle(raw)
        if len(vehicle) < 8:
            bot.reply_to(msg, "❌ Invalid registration number. Send proper format.\nExample: `MH12DE1433`", parse_mode='Markdown')
            return
        
        waiting_msg = bot.send_message(chat_id, "⏳ *This might take a few seconds... Kindly wait.*", parse_mode='Markdown')
        
        data = fetch_api4(vehicle)
        result = format_vehicle_result(data)
        
        try:
            bot.delete_message(chat_id, waiting_msg.message_id)
        except:
            pass
        
        log_search(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, "vehicle", vehicle, data)
        
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, result, parse_mode='Markdown', disable_web_page_preview=True)
        
        if data and "error" not in data and data.get('registration_number'):
            filename = export_result(data, vehicle, "vehicle")
            with open(filename, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📄 *Vehicle Report for {vehicle}*", parse_mode='Markdown')
            os.remove(filename)

# ========= MAIN =========
if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    
    try:
        bot.remove_webhook()
        print("✅ Webhook removed successfully")
    except Exception as e:
        print(f"⚠️ Webhook removal failed: {e}")
    
    time.sleep(2)
    
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
