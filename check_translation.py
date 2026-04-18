#!/usr/bin/env python3
import json, os, re, sys, sqlite3, datetime, shutil, logging, urllib.parse, time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass, field
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 10808
    proxy_url: str = ""
    proxies: Dict[str, str] = field(default_factory=dict)
    use_proxy: bool = True
    data_file: str = "table.json"
    db_file: str = ""
    server_port: int = 5382
    length_ratio_min: float = 0.3
    length_ratio_max: float = 2.5
    check_rules: Dict[str, Any] = field(default_factory=dict)
    system_title: str = "Love escalator 翻译质量检查工具"

    def __post_init__(self):
        self.proxy_url = f"socks5://{self.proxy_host}:{self.proxy_port}"
        self.proxies = {"http": self.proxy_url, "https": self.proxy_url}

config = AppConfig()
all_items = []

cache = {}
CACHE_TTL = 10  # seconds

# Translation API Configuration
DEFAULT_API = "groq"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

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
    with sqlite3.connect(config.db_file) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS translation_status (id INTEGER PRIMARY KEY, file_key TEXT, index_id INTEGER, jp TEXT, cn TEXT, is_translated INTEGER DEFAULT 0, is_fixed INTEGER DEFAULT 0, issue_type TEXT, ai_suggestion TEXT, created_at TEXT, updated_at TEXT, UNIQUE(file_key, index_id))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS groq_config (id INTEGER PRIMARY KEY CHECK (id=1), api_key TEXT, model TEXT DEFAULT 'llama-3.3-70b-versatile', target_lang TEXT DEFAULT 'zh-Hans', updated_at TEXT)''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_is_fixed ON translation_status(is_fixed)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_key ON translation_status(file_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixed_file ON translation_status(is_fixed, file_key)")
        conn.commit()

def load_groq_config():
    if not config.db_file or not os.path.exists(config.db_file): return
    try:
        with sqlite3.connect(config.db_file) as conn:
            row = conn.cursor().execute("SELECT api_key, model, target_lang FROM groq_config WHERE id=1").fetchone()
            if row:
                TRANSLATION_APIS["groq"]["api_key"] = row[0] or ""
                TRANSLATION_APIS["groq"]["model"] = row[1] or DEFAULT_MODEL
                TRANSLATION_APIS["groq"]["target_lang"] = row[2] if len(row) > 2 else "zh-Hans"
    except Exception:
        pass

def save_groq_config(api_key, model, target_lang="zh-Hans"):
    with sqlite3.connect(config.db_file) as conn:
        conn.execute("INSERT OR REPLACE INTO groq_config VALUES(1,?,?,?,?)", (api_key, model, target_lang, datetime.datetime.now().isoformat()))
        conn.commit()
    TRANSLATION_APIS["groq"]["api_key"] = api_key
    TRANSLATION_APIS["groq"]["model"] = model
    TRANSLATION_APIS["groq"]["target_lang"] = target_lang

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    config.db_file = os.path.join(script_dir, "translation_status.db")
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as f:
                c = json.load(f)
                config.data_file = c.get("data_file", "table.json")
                config.server_port = c.get("port", 5382)
                config.length_ratio_min = c.get("length_ratio_min", 0.3)
                config.length_ratio_max = c.get("length_ratio_max", 2.5)
                config.check_rules = c.get("check_rules", {})
    except Exception as e:
        print(f"配置加载失败: {e}")

def get_db_stats():
    if not os.path.exists(config.db_file): return {"exists": False, "total": 0, "translated": 0, "fixed": 0}
    with sqlite3.connect(config.db_file) as conn:
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM translation_status").fetchone()[0]
        translated = cur.execute("SELECT COUNT(*) FROM translation_status WHERE is_translated=1").fetchone()[0]
        fixed = cur.execute("SELECT COUNT(*) FROM translation_status WHERE is_fixed=1").fetchone()[0]
    return {"exists": True, "total": total, "translated": translated, "fixed": fixed}

def sync_db():
    init_db()
    data = load_data()
    now = datetime.datetime.now().isoformat()
    with sqlite3.connect(config.db_file) as conn:
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
                    cur.execute("INSERT INTO translation_status VALUES (?,?,?,?,?,?,?,?,?,?)", (None, file_key, idx, jp, cn, is_translated, is_fixed, "", now, now))
                    inserted += 1
        conn.commit()
    return {"inserted": inserted, "updated": updated}

def backup_db():
    if not os.path.exists(config.db_file): return {"error": "数据库不存在"}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(config.db_file, os.path.join(script_dir, f"translation_status_backup_{now}.db"))
    return {"success": True, "path": os.path.join(script_dir, f"translation_status_backup_{now}.db")}

def load_all_data():
    global all_items
    all_items = []
    with open(config.data_file, encoding='utf-8') as f:
        data = json.load(f)
        for file_key, items in data.items():
            if isinstance(items, list):
                for idx, item in enumerate(items):
                    all_items.append({"file": file_key, "index": idx, "item": item})
    return all_items

def load_data(): 
    with open(config.data_file, encoding='utf-8') as f:
        return json.load(f)

def count_cn(text): return len(re.sub(r'[\s\W]', '', text))

def check_single_issue(item, issue_type):
    jp, cn = item.get("jp", ""), item.get("cn", "")
    if issue_type == "cn_empty": return not cn or cn.strip() == ""
    if issue_type == "placeholder": return "「" in cn or "」" in cn or "……" in cn or "..." in cn
    if issue_type == "digit_placeholder": return bool(re.search(r'\[NUM\]|\{n\}|\d+\}', cn))
    if issue_type == "same_content": return cn == jp
    if issue_type == "low_quality": return bool(re.search(r'这个|那个|什么|怎么|为什么|如何', cn)) and count_cn(cn) < 5
    if issue_type == "length_abnormal":
        jp_len, cn_len = count_cn(jp), count_cn(cn)
        if jp_len > 0: return cn_len < jp_len * config.length_ratio_min or cn_len > jp_len * config.length_ratio_max
    return False

def translate_with_api(text, api_name=None, use_proxy=None, target_lang=None):
    if not text: return None
    api_key = api_name or DEFAULT_API
    if api_key not in TRANSLATION_APIS: return "未找到翻译引擎"
    
    # 保留换行符：将 \n 替换为占位符，AI 翻译后再还原
    text_for_translate = text.replace('\n', '{{NEWLINE}}')
    
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
                    {"role": "user", "content": text_for_translate}
                ],
                "stream": False
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key_groq}'
            }
            
            payload_str = json.dumps(payload, ensure_ascii=False)
            
            proxies = config.proxies if (use_proxy is None or use_proxy) else None
            resp = requests.post(url, data=payload_str.encode('utf-8'), headers=headers, proxies=proxies, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                translation = content.replace('{{NEWLINE}}', '\n') if content else ""
                return translation or "AI返回内容为空"
            else:
                error = resp.json().get("error", {}).get("message", resp.text[:200])
                return f"翻译失败: HTTP {resp.status_code} - {error}"
    except requests.exceptions.Timeout as e:
        return "翻译请求超时: " + str(e)[:100]
    except requests.exceptions.ProxyError as e:
        return "Proxy connection failed: " + str(e)[:100]
    except UnicodeEncodeError as e:
        return "Translation encoding error: " + str(e)
    except Exception as e:
        return "Translation failed: " + str(e)
    return "翻译服务暂不可用"

def load_template():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载模板失败: {e}")
        return "<html><body><h1>模板加载失败</h1></body></html>"

try:
    HTML_TEMPLATE = load_template().replace('content="20240416"', 'content="' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '"').replace('翻译质量检查工具', '{{SYSTEM_TITLE}}')
except Exception:
    HTML_TEMPLATE = "<html><body><h1>模板加载失败</h1></body></html>"

def load_settings_template():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, 'templates', 'settings.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载设置模板失败: {e}")
        return "<html><body><h1>设置模板加载失败</h1></body></html>"

try:
    SETTINGS_TEMPLATE = load_settings_template().replace('content="20240416"', 'content="' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '"').replace('翻译质量检查工具', '{{SYSTEM_TITLE}}')
except Exception:
    SETTINGS_TEMPLATE = "<html><body><h1>设置模板加载失败</h1></body></html>"

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
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.replace('{{SYSTEM_TITLE}}', config.system_title).encode('utf-8'))
        elif self.path == '/settings.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(SETTINGS_TEMPLATE.replace('{{SYSTEM_TITLE}}', config.system_title).encode('utf-8'))
        elif self.path == '/tutorial.html':
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(script_dir, 'templates', 'tutorial.html'), 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                logger.error(f"加载教程页面失败: {e}")
                self.send_error(500)
        elif self.path.startswith('/api/all'):
            try:
                query = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
                page = max(1, int(query.get('page', ['1'])[0]))
                size = min(max(1, int(query.get('size', ['100'])[0])), 500)
                start = (page - 1) * size
                end = start + size
                total = len(all_items)
                items = [{"file": e["file"], "index": e["index"], "item": e["item"], "issues": []} for e in all_items[start:end]]
                self.send_json({"total": total, "page": page, "size": size, "items": items})
            except (ValueError, KeyError) as e:
                logger.error(f"分页参数错误: {e}")
                self.send_json({"error": "Invalid pagination parameters"})
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
                "target_lang": api_config.get("target_lang", "zh-Hans")
            })
        elif self.path == '/api/proxy/status':
            self.send_json({"enabled": config.use_proxy})
        elif self.path.startswith('/api/next'):
            query = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
            show_fixed = query.get('show_fixed', ['0'])[0]
            filter_long_cn = query.get('filter_long_cn', ['0'])[0]
            cache_key = f"next:{show_fixed}:{filter_long_cn}"
            now = time.time()
            if cache_key in cache and now - cache[cache_key]["ts"] < CACHE_TTL:
                self.send_json(cache[cache_key]["data"])
                return
            with sqlite3.connect(config.db_file) as conn:
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
                results = [{"id": r[0], "file": r[1], "index": r[2], "item": {"jp": r[3], "cn": r[4]}, "is_fixed": r[5]} for r in rows]
            response_data = {"total": len(results), "items": results}
            cache[cache_key] = {"data": response_data, "ts": now}
            self.send_json(response_data)
        elif self.path.startswith('/api/search?'):
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            keyword = query.get('keyword', [''])[0]
            search_type = query.get('type', ['all'])[0]
            filter_long_cn = query.get('filter_long_cn', ['0'])[0]
            with sqlite3.connect(config.db_file) as conn:
                cur = conn.cursor()
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
                results = [{"id": r[0], "file": r[1], "index": r[2], "item": {"jp": r[3], "cn": r[4]}} for r in rows]
            self.send_json({"results": results, "total": len(results)})
        else: self.send_error(404)
    
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
        except (ValueError, TypeError):
            self.send_json({"error": "Invalid Content-Length"})
            return
        if length > 1024 * 1024:
            self.send_json({"error": "Request body too large"})
            return
        try:
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"})
            return
        
        if self.path == '/api/db/init': self.send_json(sync_db())
        elif self.path == '/api/db/backup': self.send_json(backup_db())
        elif self.path == '/api/db/sync-jp':
            try:
                with open(config.data_file, 'r', encoding='utf-8') as f:
                    table_data = json.load(f)
                with sqlite3.connect(config.db_file) as conn:
                    cur = conn.cursor()
                    updated = 0
                    for file_key, items in table_data.items():
                        if not isinstance(items, list): continue
                        for idx, item in enumerate(items):
                            jp = item.get('jp', '')
                            cur.execute("UPDATE translation_status SET jp=? WHERE file_key=? AND index_id=?", (jp, file_key, idx))
                            if cur.rowcount > 0: updated += 1
                    conn.commit()
                self.send_json({"success": True, "updated": updated})
            except Exception as e:
                logger.error(f"同步原文失败: {e}")
                self.send_json({"error": str(e)})
        elif self.path == '/api/db/sync-cn':
            try:
                with open(config.data_file, 'r', encoding='utf-8') as f:
                    table_data = json.load(f)
                with sqlite3.connect(config.db_file) as conn:
                    cur = conn.cursor()
                    updated = 0
                    for file_key, items in table_data.items():
                        if not isinstance(items, list): continue
                        for idx, item in enumerate(items):
                            cn = item.get('cn', '')
                            is_translated = 1 if cn and cn.strip() else 0
                            cur.execute("UPDATE translation_status SET cn=?, is_translated=? WHERE file_key=? AND index_id=?", (cn, is_translated, file_key, idx))
                            if cur.rowcount > 0: updated += 1
                    conn.commit()
                self.send_json({"success": True, "updated": updated})
            except Exception as e:
                logger.error(f"同步翻译失败: {e}")
                self.send_json({"error": str(e)})
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
            file_key = data.get("file")
            idx = data.get("index")
            new_cn = data.get("cn", "")
            if not file_key or idx is None:
                self.send_json({"error": "Missing file or index"})
                return
            now = datetime.datetime.now().isoformat()
            is_translated = 1 if new_cn and new_cn.strip() else 0
            is_fixed = 1
            
            # 更新数据库
            with sqlite3.connect(config.db_file) as conn:
                conn.execute("UPDATE translation_status SET cn=?, is_translated=?, is_fixed=?, updated_at=? WHERE file_key=? AND index_id=?", (new_cn, is_translated, is_fixed, now, file_key, idx))
                conn.commit()
            
            # 同时更新 table.json
            try:
                with open(config.data_file, 'r', encoding='utf-8') as f:
                    table_data = json.load(f)
                if file_key in table_data and isinstance(table_data[file_key], list) and idx < len(table_data[file_key]):
                    table_data[file_key][idx]['cn'] = new_cn
                    with open(config.data_file, 'w', encoding='utf-8') as f:
                        json.dump(table_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"更新 table.json 失败: {e}")
            
            cache.clear()
            self.send_json({"success": True})
        elif self.path == '/api/translate': self.send_json({"translation": translate_with_api(data.get("text", ""), data.get("api", DEFAULT_API), data.get("useProxy"), data.get("targetLang"))})
        elif self.path == '/api/groq/config': 
            save_groq_config(data.get("apiKey", ""), data.get("model", DEFAULT_MODEL), data.get("targetLang", "zh-Hans"))
            self.send_json({"success": True})
        elif self.path == '/api/proxy/config': config.use_proxy = data.get("enabled", False); self.send_json({"success": True, "enabled": config.use_proxy})
        else: self.send_error(404)

def run_server(port=None):
    port = port or config.server_port
    server = HTTPServer(('0.0.0.0', port), Handler)
    logger.info(f"服务已启动: http://localhost:{port}")
    print("按 Ctrl+C 停止服务", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止", flush=True)
        server.shutdown()

if __name__ == "__main__":
    try:
        load_config()
        init_db()
        load_groq_config()
        load_all_data()
    except Exception as e:
        print(f"初始化失败: {e}", flush=True)
        sys.exit(1)
    
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else None
    run_server(port)
