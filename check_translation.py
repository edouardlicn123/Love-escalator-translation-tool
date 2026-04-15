#!/usr/bin/env python3
import json, os, re, sys, sqlite3, datetime, shutil, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_FILE = CONFIG_FILE = DB_FILE = HF_TOKEN = None
SERVER_PORT = 5000
HF_MODEL = None
LENGTH_RATIO_MIN, LENGTH_RATIO_MAX = 0.3, 2.5
CHECK_RULES, AVAILABLE_MODELS = {}, []
TRANSLATION_APIS, DEFAULT_API = {}, "doubao"
issues_list, all_items = [], []

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS translation_status (id INTEGER PRIMARY KEY, file_key TEXT, index_id INTEGER, jp TEXT, cn TEXT, is_translated INTEGER DEFAULT 0, is_fixed INTEGER DEFAULT 0, issue_type TEXT, ai_suggestion TEXT, created_at TEXT, updated_at TEXT, UNIQUE(file_key, index_id))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS doubao_config (id INTEGER PRIMARY KEY CHECK (id=1), api_url TEXT, session_id TEXT, updated_at TEXT)''')
    conn.commit(); conn.close()

def load_doubao_config():
    global TRANSLATION_APIS
    if not DB_FILE or not os.path.exists(DB_FILE): return
    conn = sqlite3.connect(DB_FILE)
    row = conn.cursor().execute("SELECT api_url, session_id FROM doubao_config WHERE id=1").fetchone()
    conn.close()
    if row:
        if "doubao" not in TRANSLATION_APIS: TRANSLATION_APIS["doubao"] = {"name": "豆包AI (免费)", "method": "POST", "type": "openai"}
        TRANSLATION_APIS["doubao"]["url"], TRANSLATION_APIS["doubao"]["session"] = row[0] or "", row[1] or ""

def save_doubao_config(api_url, session_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO doubao_config VALUES(1,?,?,?)", (api_url, session_id, datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()
    global TRANSLATION_APIS
    TRANSLATION_APIS["doubao"]["url"] = api_url
    TRANSLATION_APIS["doubao"]["session"] = session_id

def load_config():
    global DATA_FILE, CONFIG_FILE, HF_TOKEN, SERVER_PORT, HF_MODEL, LENGTH_RATIO_MIN, LENGTH_RATIO_MAX, CHECK_RULES, AVAILABLE_MODELS, DB_FILE, TRANSLATION_APIS, DEFAULT_API
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    db_path = os.path.join(script_dir, "translation_status.db")
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as f:
                c = json.load(f)
                DATA_FILE = c.get("data_file", "/home/edo/translation/table.json")
                CONFIG_FILE = c.get("config_file", config_path)
                HF_TOKEN = c.get("hf_token", "")
                SERVER_PORT = c.get("port", 5000)
                HF_MODEL = c.get("hf_model", "")
                LENGTH_RATIO_MIN = c.get("length_ratio_min", 0.3)
                LENGTH_RATIO_MAX = c.get("length_ratio_max", 2.5)
                CHECK_RULES = c.get("check_rules", {})
                AVAILABLE_MODELS = c.get("available_models", [])
                TRANSLATION_APIS = c.get("translation_apis", {})
                DEFAULT_API = c.get("default_api", "doubao")
        DB_FILE = db_path
    except Exception as e:
        print(f"配置加载失败: {e}")
        DATA_FILE, CONFIG_FILE, DB_FILE = "/home/edo/translation/table.json", config_path, db_path
        HF_TOKEN, SERVER_PORT = "", 5000
        DEFAULT_API = "doubao"
        TRANSLATION_APIS = {"doubao": {"name": "豆包AI (免费)", "url": "", "method": "POST", "session": "", "type": "openai"}}
        LENGTH_RATIO_MIN, LENGTH_RATIO_MAX = 0.3, 2.5

def get_db_stats():
    if not os.path.exists(DB_FILE): return {"exists": False, "total": 0, "translated": 0, "fixed": 0}
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM translation_status").fetchone()[0]
    translated = cur.execute("SELECT COUNT(*) FROM translation_status WHERE is_translated=1").fetchone()[0]
    fixed = cur.execute("SELECT COUNT(*) FROM translation_status WHERE is_fixed=1").fetchone()[0]
    conn.close()
    return {"exists": True, "total": total, "translated": translated, "fixed": fixed}

def sync_db():
    init_db()
    data = load_data()
    now = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    inserted = updated = 0
    for file_key, items in data.items():
        if not isinstance(items, list): continue
        for idx, item in enumerate(items):
            jp, cn = item.get("jp", ""), item.get("cn", "")
            is_translated = 1 if cn and cn.strip() else 0
            issue = check_single_issue_type(item)
            row = cur.execute("SELECT is_fixed FROM translation_status WHERE file_key=? AND index_id=?", (file_key, idx)).fetchone()
            was_fixed = row[0] if row else 0
            is_fixed = was_fixed if (issue and was_fixed) else (1 if not issue else 0)
            if row:
                cur.execute("UPDATE translation_status SET cn=?, is_translated=?, is_fixed=?, issue_type=? WHERE file_key=? AND index_id=?", (cn, is_translated, is_fixed, issue, file_key, idx))
                updated += 1
            else:
                cur.execute("INSERT INTO translation_status VALUES (?,?,?,?,?,?,?,?,?,?)", (None, file_key, idx, jp, cn, is_translated, is_fixed, issue, now, now))
                inserted += 1
    conn.commit(); conn.close()
    return {"inserted": inserted, "updated": updated}

def backup_db():
    if not os.path.exists(DB_FILE): return {"error": "数据库不存在"}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB_FILE, os.path.join(script_dir, f"translation_status_backup_{now}.db"))
    return {"success": True, "path": os.path.join(script_dir, f"translation_status_backup_{now}.db")}

def load_all_data():
    global all_items
    all_items = []
    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)
        for file_key, items in data.items():
            if isinstance(items, list):
                for idx, item in enumerate(items):
                    all_items.append({"file": file_key, "index": idx, "item": item})
    return all_items

def load_data(): return json.load(open(DATA_FILE, encoding='utf-8'))
def save_data(data): json.dump(data, open(DATA_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
def count_cn(text): return len(re.sub(r'[\s\W]', '', text))

def check_single_issue_type(item):
    jp, cn = item.get("jp", ""), item.get("cn", "")
    issues = []
    if not cn or cn.strip() == "": issues.append("cn_empty")
    if "「" in cn or "」" in cn or "……" in cn or "..." in cn: issues.append("placeholder")
    if re.search(r'\[NUM\]|\{n\}|\d+\}', cn): issues.append("digit_placeholder")
    if cn == jp and cn: issues.append("same_content")
    if re.search(r'这个|那个|什么|怎么|为什么|如何', cn) and count_cn(cn) < 5: issues.append("low_quality")
    jp_len, cn_len = count_cn(jp), count_cn(cn)
    if jp_len > 0 and (cn_len < jp_len * LENGTH_RATIO_MIN or cn_len > jp_len * LENGTH_RATIO_MAX): issues.append("length_abnormal")
    return ",".join(issues) if issues else ""

def check_single_issue(item, issue_type):
    jp, cn = item.get("jp", ""), item.get("cn", "")
    if issue_type == "cn_empty": return not cn or cn.strip() == ""
    if issue_type == "placeholder": return "「" in cn or "」" in cn or "……" in cn or "..." in cn
    if issue_type == "digit_placeholder": return bool(re.search(r'\[NUM\]|\{n\}|\d+\}', cn))
    if issue_type == "same_content": return cn == jp
    if issue_type == "low_quality": return bool(re.search(r'这个|那个|什么|怎么|为什么|如何', cn)) and count_cn(cn) < 5
    if issue_type == "length_abnormal":
        jp_len, cn_len = count_cn(jp), count_cn(cn)
        if jp_len > 0: return cn_len < jp_len * LENGTH_RATIO_MIN or cn_len > jp_len * LENGTH_RATIO_MAX
    return False

def translate_with_api(text, api_name=None):
    if not text: return None
    api_key = api_name or DEFAULT_API
    if api_key not in TRANSLATION_APIS: return "未找到翻译引擎"
    try:
        api_config = TRANSLATION_APIS.get(api_key, {})
        url, session = api_config.get("url", ""), api_config.get("session", "")
        if api_key == "doubao":
            if not url: return "请先在设置中填写豆包API地址"
            if not session: return "请先在设置中填写豆包SessionID"
            payload = {"model": "doubao", "messages": [{"role": "system", "content": "你是一个专业翻译助手，将用户输入的日文翻译成中文，只返回翻译结果，不要任何解释。"}, {"role": "user", "content": text}], "stream": False}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {session}'}, method='POST')
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    result = json.loads(resp.read().decode('utf-8'))
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e: return f"翻译失败: {str(e)}"
    return "翻译服务暂不可用"

def translate_deeplx(text): return translate_with_api(text, "doubao")
def translate_hf(text): return translate_with_api(text, "doubao")

def load_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()

HTML_TEMPLATE = load_template()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/all':
            self.send_json({"total": len(all_items), "items": [{"file": e["file"], "index": e["index"], "item": e["item"], "issues": []} for e in all_items]})
        elif self.path == '/api/models': self.send_json({"models": AVAILABLE_MODELS})
        elif self.path == '/api/translation-apis': self.send_json({"apis": [{"key": k, "name": v.get("name", k)} for k, v in TRANSLATION_APIS.items()], "default": DEFAULT_API})
        elif self.path == '/api/db/stats': self.send_json(get_db_stats())
        elif self.path == '/api/doubao/status':
            api_config = TRANSLATION_APIS.get("doubao", {})
            self.send_json({"configured": bool(api_config.get("url", "")) and bool(api_config.get("session", "")), "has_url": bool(api_config.get("url", "")), "has_session": bool(api_config.get("session", ""))})
        else: self.send_error(404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        if self.path == '/api/db/init': self.send_json(sync_db())
        elif self.path == '/api/db/backup': self.send_json(backup_db())
        elif self.path == '/api/filter':
            rules, api_source = data.get("rules", []), data.get("api", "")
            global DEFAULT_API, issues_list, all_items
            if api_source: DEFAULT_API = api_source
            api_source = api_source or DEFAULT_API
            if rules:
                results = []
                for entry in all_items:
                    item, file_key, idx = entry["item"], entry["file"], entry["index"]
                    item_issues = [rule for rule in rules if rule in ["cn_empty", "placeholder", "digit_placeholder", "same_content", "low_quality", "length_abnormal"] and check_single_issue(item, rule)]
                    if item_issues: results.append({"file": file_key, "index": idx, "item": item, "issues": item_issues})
                issues_list = results
            else: issues_list = [{"file": e["file"], "index": e["index"], "item": e["item"], "issues": []} for e in all_items]
            self.send_json({"total": len(issues_list), "issues": issues_list})
        elif self.path == '/api/update':
            full_data = load_data()
            file_key, idx, new_cn = data.get("file"), data.get("index"), data.get("cn")
            if file_key in full_data and idx < len(full_data[file_key]):
                full_data[file_key][idx]["cn"] = new_cn
                save_data(full_data)
                conn = sqlite3.connect(DB_FILE)
                now = datetime.datetime.now().isoformat()
                is_translated = 1 if new_cn and new_cn.strip() else 0
                issue = check_single_issue_type(full_data[file_key][idx])
                is_fixed = 0 if issue else 1
                conn.execute("INSERT OR REPLACE INTO translation_status VALUES (?,?,?,?,?,?,?,?)", (None, file_key, idx, new_cn, is_translated, is_fixed, issue, now))
                conn.commit(); conn.close()
                self.send_json({"success": True})
            else: self.send_json({"error": "Item not found"})
        elif self.path == '/api/translate': self.send_json({"translation": translate_with_api(data.get("text", ""), data.get("api", DEFAULT_API))})
        elif self.path == '/api/token': self.send_json({"success": True})
        elif self.path == '/api/doubao/config': save_doubao_config(data.get("url", ""), data.get("session", "")); self.send_json({"success": True})
        else: self.send_error(404)

def run_server(port=None):
    port = port or SERVER_PORT
    try:
        server = HTTPServer(('0.0.0.0', port), Handler)
        print(f"服务已启动: http://localhost:{port}", flush=True)
        server.serve_forever()
    except Exception as e: print(f"启动失败: {e}", flush=True)

if __name__ == "__main__":
    load_config()
    init_db()
    load_doubao_config()
    load_all_data()
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else None
    run_server(port)
