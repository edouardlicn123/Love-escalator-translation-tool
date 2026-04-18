# 同步按钮替换计划

## 需求
将工具栏的"建立数据库"和"备份数据库"按钮替换为"同步原文"和"同步翻译"按钮，同时保持 start.sh 的兼容性。

---

## 当前状态

### 工具栏按钮 (index.html 第86-91行)
```html
<button onclick="initDb()">建立数据库</button>
<button onclick="backupDb()">备份数据库</button>
```

### start.sh 调用的接口
- `/api/db/init` → 调用 sync_db() 初始化数据库
- `/api/db/backup` → 调用 backup_db() 备份数据库

---

## 修改方案

### 1. 前端修改 (index.html)

**按钮替换**:
```html
<button onclick="syncJpFromSource()">同步原文</button>
<button onclick="syncCnFromSource()">同步翻译</button>
```

**新增函数**:
```javascript
async function syncJpFromSource() {
    // 调用 /api/db/sync-jp
}

async function syncCnFromSource() {
    // 调用 /api/db/sync-cn
}
```

### 2. 后端修改 (check_translation.py)

**保留现有接口** (保持 start.sh 兼容):
- `/api/db/init` - 继续调用 sync_db()
- `/api/db/backup` - 继续调用 backup_db()

**新增接口**:
- `/api/db/sync-jp` - 从 table.json 读取 jp，同步到数据库
- `/api/db/sync-cn` - 从 table.json 读取 cn，同步到数据库

### 3. start.sh 兼容性

start.sh 中的 "初始化数据库" 选项调用 `/api/db/init`，这个功能保留不变，用户仍可通过 start.sh 初始化数据库。

---

## 详细实现

### 后端: /api/db/sync-jp
```python
elif self.path == '/api/db/sync-jp':
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
                updated += cur.rowcount
        conn.commit()
    
    self.send_json({"success": True, "updated": updated})
```

### 后端: /api/db/sync-cn
```python
elif self.path == '/api/db/sync-cn':
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
                updated += cur.rowcount
        conn.commit()
    
    self.send_json({"success": True, "updated": updated})
```

---

## 预计改动

| 文件 | 改动 |
|------|------|
| index.html | 替换2个按钮 + 新增2个函数 (~20行) |
| check_translation.py | 新增2个API接口 (~30行) |

---

## 执行顺序

1. 后端添加 `/api/db/sync-jp` 和 `/api/db/sync-cn` 接口
2. 前端替换按钮和添加函数
3. 测试验证

---

## 确认事项

- start.sh 的 "初始化数据库" 功能保持不变 ✓
- 原有的 `/api/db/init` 和 `/api/db/backup` 接口保持不变 ✓
- 仅替换前端按钮，不影响后端现有功能 ✓
