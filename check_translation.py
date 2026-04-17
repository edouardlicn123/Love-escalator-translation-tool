#!/usr/bin/env python3
import json, os, re, sys, sqlite3, datetime, shutil, urllib.request, urllib.error
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 10808
PROXY_URL = f"socks5://{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}

USE_PROXY = True

DATA_FILE = CONFIG_FILE = DB_FILE = None
SERVER_PORT = 5000
LENGTH_RATIO_MIN, LENGTH_RATIO_MAX = 0.3, 2.5
CHECK_RULES = {}
issues_list, all_items = [], []

TRANSLATION_APIS = {
    "groq": {
        "name": "Groq API (推荐)",
        "url": "https://api.groq.com/openai/v1",
        "model": "llama-3.1-8b-instant",
        "target_lang": "zh-Hans",
        "system_title": "Love escalator 翻译质量检查工具"
    }
}
DEFAULT_API = "groq"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
SYSTEM_TITLE = "Love escalator 翻译质量检查工具"

LANG_MAP = {
    "en": "English",
    "fr": "French (français)",
    "de": "German (deutsch)",
    "es": "Spanish (español)",
    "pt": "Portuguese (português)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "zh-Hant": "Traditional Chinese (繁體中文)",
    "zh-Hans": "Simplified Chinese (简体中文)"
}

TRANSLATION_APIS = {
    "groq": {
        "name": "Groq API (推荐)",
        "url": "https://api.groq.com/openai/v1",
        "model": DEFAULT_MODEL,
        "target_lang": "zh-Hans"
    }
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS translation_status (id INTEGER PRIMARY KEY, file_key TEXT, index_id INTEGER, jp TEXT, cn TEXT, is_translated INTEGER DEFAULT 0, is_fixed INTEGER DEFAULT 0, issue_type TEXT, ai_suggestion TEXT, created_at TEXT, updated_at TEXT, UNIQUE(file_key, index_id))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS groq_config (id INTEGER PRIMARY KEY CHECK (id=1), api_key TEXT, model TEXT DEFAULT 'llama-3.3-70b-versatile', target_lang TEXT DEFAULT 'zh-Hans', updated_at TEXT, system_title TEXT DEFAULT 'Love escalator 翻译质量检查工具')''')
    try:
        conn.execute("ALTER TABLE groq_config ADD COLUMN target_lang TEXT DEFAULT 'zh-Hans'")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE groq_config ADD COLUMN system_title TEXT DEFAULT '翻译质量检查工具'")
    except sqlite3.OperationalError:
        pass
    conn.commit(); conn.close()

def load_groq_config():
    if not DB_FILE or not os.path.exists(DB_FILE): return
    row = None
    try:
        conn = sqlite3.connect(DB_FILE)
        try:
            row = conn.cursor().execute("SELECT api_key, model, target_lang, system_title FROM groq_config WHERE id=1").fetchone()
        except sqlite3.OperationalError:
            row = conn.cursor().execute("SELECT api_key, model FROM groq_config WHERE id=1").fetchone()
            if row:
                row = (row[0], row[1], "zh-Hans", "Love escalator 翻译质量检查工具")
        finally:
            conn.close()
    except Exception:
        pass
    if row:
        TRANSLATION_APIS["groq"]["api_key"] = row[0] or ""
        TRANSLATION_APIS["groq"]["model"] = row[1] or DEFAULT_MODEL
        TRANSLATION_APIS["groq"]["target_lang"] = row[2] if len(row) > 2 else "zh-Hans"
        if len(row) > 3:
            TRANSLATION_APIS["groq"]["system_title"] = row[3]

SYSTEM_TITLE = TRANSLATION_APIS["groq"].get("system_title", "Love escalator 翻译质量检查工具")

def save_groq_config(api_key, model, target_lang="zh-Hans", system_title="Love escalator 翻译质量检查工具"):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if api_key == "(已有)":
        old = cur.execute("SELECT api_key FROM groq_config WHERE id=1").fetchone()
        api_key = old[0] if old else ""
    cur.execute("INSERT OR REPLACE INTO groq_config VALUES(1,?,?,?,?,?)", (api_key, model, target_lang, datetime.datetime.now().isoformat(), system_title))
    conn.commit(); conn.close()
    TRANSLATION_APIS["groq"]["api_key"] = api_key
    TRANSLATION_APIS["groq"]["model"] = model
    TRANSLATION_APIS["groq"]["target_lang"] = target_lang
    TRANSLATION_APIS["groq"]["system_title"] = system_title

def load_config():
    global DATA_FILE, CONFIG_FILE, SERVER_PORT, LENGTH_RATIO_MIN, LENGTH_RATIO_MAX, CHECK_RULES, DB_FILE
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "translation_status.db")
    config_path = os.path.join(script_dir, "config.json")
    
    # 默认值
    DATA_FILE = "table.json"
    SERVER_PORT = 5382
    LENGTH_RATIO_MIN = 0.3
    LENGTH_RATIO_MAX = 2.5
    CHECK_RULES = {}
    DB_FILE = db_path
    
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as f:
                c = json.load(f)
                DATA_FILE = c.get("data_file", "table.json")
                SERVER_PORT = c.get("port", 5382)
                LENGTH_RATIO_MIN = c.get("length_ratio_min", 0.3)
                LENGTH_RATIO_MAX = c.get("length_ratio_max", 2.5)
                CHECK_RULES = c.get("check_rules", {})
    except Exception as e:
        print(f"配置加载失败: {e}")

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
            is_fixed = 0
            if row := cur.execute("SELECT is_fixed FROM translation_status WHERE file_key=? AND index_id=?", (file_key, idx)).fetchone():
                cur.execute("UPDATE translation_status SET jp=?, cn=?, is_translated=?, is_fixed=? WHERE file_key=? AND index_id=?", (jp, cn, is_translated, is_fixed, file_key, idx))
                updated += 1
            else:
                cur.execute("INSERT INTO translation_status (file_key, index_id, jp, cn, is_translated, is_fixed, issue_type, ai_suggestion, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (file_key, idx, jp, cn, is_translated, is_fixed, "", "", now, now))
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

def translate_with_api(text, api_name=None, use_proxy=None, target_lang=None):
    if not text: return None
    api_key = api_name or DEFAULT_API
    if api_key not in TRANSLATION_APIS: return "未找到翻译引擎"
    try:
        api_config = TRANSLATION_APIS.get(api_key, {})
        
        if api_key == "groq":
            api_key_groq = api_config.get("api_key", "")
            if not api_key_groq: return "请先在设置中填写Groq API Key"
            
            model_name = api_config.get("model", DEFAULT_MODEL)
            base_url = api_config.get("url", "https://api.groq.com/openai/v1")
            url = f"{base_url}/chat/completions"
            
            lang = target_lang or api_config.get("target_lang", "zh-Hans")
            lang_name = LANG_MAP.get(lang, "Simplified Chinese (简体中文)")
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": f"You are a professional translator. Translate the following Japanese text to {lang_name}. Only return the translation, no explanations."},
                    {"role": "user", "content": text}
                ],
                "stream": False
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key_groq}'
            }
            
            import json
            payload_str = json.dumps(payload, ensure_ascii=False)
            
            proxies = PROXIES if (use_proxy if use_proxy is not None else USE_PROXY) else None
            resp = requests.post(url, data=payload_str.encode('utf-8'), headers=headers, proxies=proxies, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content or "AI返回内容为空"
            else:
                error = resp.json().get("error", {}).get("message", resp.text[:200])
                return f"翻译失败: HTTP {resp.status_code} - {error}"
    except requests.exceptions.ProxyError as e:
        return "Proxy connection failed: " + str(e)[:100]
    except UnicodeEncodeError as e:
        return "Translation encoding error: " + str(e)
    except Exception as e:
        return "Translation failed: " + str(e)
    return "翻译服务暂不可用"

def load_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()

HTML_TEMPLATE = load_template().replace('content="20240416"', 'content="' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '"').replace('翻译质量检查工具', '{{SYSTEM_TITLE}}')

def load_settings_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'templates', 'settings.html'), 'r', encoding='utf-8') as f:
        return f.read()

SETTINGS_TEMPLATE = load_settings_template().replace('content="20240416"', 'content="' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '"').replace('翻译质量检查工具', '{{SYSTEM_TITLE}}')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_GET(self):
        global SYSTEM_TITLE
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.replace('{{SYSTEM_TITLE}}', SYSTEM_TITLE).encode('utf-8'))
        elif self.path == '/settings.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(SETTINGS_TEMPLATE.replace('{{SYSTEM_TITLE}}', SYSTEM_TITLE).encode('utf-8'))
        elif self.path == '/tutorial.html':
            script_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(script_dir, 'templates', 'tutorial.html'), 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        elif self.path == '/settings.html':
            script_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(script_dir, 'templates', 'settings.html'), 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        elif self.path == '/api/all':
            self.send_json({"total": len(all_items), "items": [{"file": e["file"], "index": e["index"], "item": e["item"], "issues": []} for e in all_items]})
        elif self.path == '/api/models': self.send_json({"models": []})
        elif self.path == '/api/translation-apis': self.send_json({"apis": [{"key": k, "name": v.get("name", k)} for k, v in TRANSLATION_APIS.items()], "default": DEFAULT_API})
        elif self.path == '/api/db/stats': self.send_json(get_db_stats())
        elif self.path == '/api/groq/status':
            api_config = TRANSLATION_APIS.get("groq", {})
            has_key = bool(api_config.get("api_key", ""))
            self.send_json({
                "configured": has_key, 
                "has_key": has_key,
                "model": api_config.get("model", DEFAULT_MODEL),
                "target_lang": api_config.get("target_lang", "zh-Hans"),
                "system_title": api_config.get("system_title", "翻译质量检查工具")
            })
        elif self.path == '/api/proxy/status':
            self.send_json({"enabled": USE_PROXY})
        elif self.path.startswith('/api/next'):
            import urllib.parse
            query = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
            show_fixed = query.get('show_fixed', ['0'])[0]
            filter_long_cn = query.get('filter_long_cn', ['0'])[0]
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            if show_fixed == '1':
                sql = "SELECT id, file_key, index_id, jp, cn, is_fixed FROM translation_status"
                if filter_long_cn == '1':
                    sql += " WHERE LENGTH(cn) > LENGTH(jp)"
                sql += " ORDER BY id"
                rows = cur.execute(sql).fetchall()
            else:
                sql = "SELECT id, file_key, index_id, jp, cn, is_fixed FROM translation_status WHERE is_fixed=0"
                if filter_long_cn == '1':
                    sql += " AND LENGTH(cn) > LENGTH(jp)"
                sql += " ORDER BY id"
                rows = cur.execute(sql).fetchall()
            conn.close()
            results = [{"id": r[0], "file": r[1], "index": r[2], "item": {"jp": r[3], "cn": r[4]}, "is_fixed": r[5]} for r in rows]
            self.send_json({"total": len(results), "items": results})
        elif self.path.startswith('/api/search?'):
            import urllib.parse
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            keyword = query.get('keyword', [''])[0]
            search_type = query.get('type', ['all'])[0]
            filter_long_cn = query.get('filter_long_cn', ['0'])[0]
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            
            # 构建WHERE条件
            where_parts = []
            params = []
            if search_type == 'unfixed':
                where_parts.append('is_fixed=0')
            if filter_long_cn == '1':
                where_parts.append('LENGTH(cn) > LENGTH(jp)')
            if keyword:
                where_parts.append('(jp LIKE ? OR cn LIKE ?)')
                params.extend(['%' + keyword + '%', '%' + keyword + '%'])
            
            where_sql = ' AND '.join(where_parts) if where_parts else '1=1'
            sql = f"SELECT id, file_key, index_id, jp, cn FROM translation_status WHERE {where_sql} LIMIT 100"
            rows = cur.execute(sql, params).fetchall()
            conn.close()
            results = [{"id": r[0], "file": r[1], "index": r[2], "item": {"jp": r[3], "cn": r[4]}} for r in rows]
            self.send_json({"results": results, "total": len(results)})
        else: self.send_error(404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        if self.path == '/api/db/init': self.send_json(sync_db())
        elif self.path == '/api/db/backup': self.send_json(backup_db())
        elif self.path == '/api/filter':
            rules = data.get("rules", [])
            if rules:
                results = []
                for entry in all_items:
                    item, file_key, idx = entry["item"], entry["file"], entry["index"]
                    item_issues = [rule for rule in rules if rule in ["cn_empty", "placeholder", "digit_placeholder", "same_content", "low_quality", "length_abnormal"] and check_single_issue(item, rule)]
                    if item_issues: results.append({"file": file_key, "index": idx, "item": item, "issues": item_issues})
                issues_list = results
            else:
                issues_list = [{"file": e["file"], "index": e["index"], "item": e["item"], "issues": []} for e in all_items]
            self.send_json({"total": len(issues_list), "issues": issues_list})
        elif self.path == '/api/update':
            full_data = load_data()
            file_key = data.get("file")
            idx = data.get("index")
            new_cn = data.get("cn", "")
            if not file_key or idx is None:
                self.send_json({"error": "Missing file or index"})
                return
            if file_key in full_data and idx < len(full_data[file_key]):
                full_data[file_key][idx]["cn"] = new_cn
                save_data(full_data)
                conn = sqlite3.connect(DB_FILE)
                now = datetime.datetime.now().isoformat()
                is_translated = 1 if new_cn and new_cn.strip() else 0
                is_fixed = 1
                conn.execute("INSERT OR REPLACE INTO translation_status (file_key, index_id, cn, is_translated, is_fixed, issue_type, updated_at) VALUES (?,?,?,?,?,?,?)", (file_key, idx, new_cn, is_translated, is_fixed, "", now))
                conn.commit(); conn.close()
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Item not found"})
        elif self.path == '/api/translate': self.send_json({"translation": translate_with_api(data.get("text", ""), data.get("api", DEFAULT_API), data.get("useProxy"), data.get("targetLang"))})
        elif self.path == '/api/groq/config': 
            save_groq_config(data.get("apiKey", ""), data.get("model", DEFAULT_MODEL), data.get("targetLang", "zh-Hans"), data.get("systemTitle", "翻译质量检查工具")); 
            global SYSTEM_TITLE
            SYSTEM_TITLE = data.get("systemTitle", "翻译质量检查工具")
            self.send_json({"success": True})
        elif self.path == '/api/proxy/config': global USE_PROXY; USE_PROXY = data.get("enabled", False); self.send_json({"success": True, "enabled": USE_PROXY})
        else: self.send_error(404)

def run_server(port=None):
    port = port or SERVER_PORT
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"服务已启动: http://localhost:{port}", flush=True)
    print("按 Ctrl+C 停止服务", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止", flush=True)
        server.shutdown()

if __name__ == "__main__":
    load_config()
    init_db()
    load_groq_config()
    load_all_data()
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else None
    run_server(port)
