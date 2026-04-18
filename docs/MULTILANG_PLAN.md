# 多语言支持计划 / Multilingual Support Plan

## 目标 / Goals

1. **start.sh**: 全部内容改为英语 / All content in English
2. **界面**: 默认为英语，语言存储在数据库 / Default to English, language stored in database
3. 单模板多语言 / Single template with multilingual support

---

## Part 1: start.sh 英语化 / English Translation

### 修改清单 / Modification List

| Line | Chinese | English |
|------|---------|---------|
| 2 | 翻译质量检查工具 - 启动脚本 | Translation Quality Check Tool - Startup Script |
| 31 | 正在安装依赖... | Installing dependencies... |
| 36 | ✓ requests, pysocks 已安装 | ✓ requests, pysocks installed |
| 38 | ✓ 依赖已安装 | ✓ Dependencies installed |
| 43 | 正在初始化数据库... | Initializing database... |
| 46 | ✗ 错误: table.json 不存在 | ✗ Error: table.json not found |
| 59-60 | 插入/更新 n 条 | Inserted/Updated n entries |
| 65 | 正在启动服务器... | Starting server... |
| 68 | ⚠ 警告: requests 未安装 | ⚠ Warning: requests not installed |
| 74 | ✗ 错误: sqlite3 不可用 | ✗ Error: sqlite3 not available |
| 79 | ✗ 错误: table.json 不存在 | ✗ Error: table.json not found |
| 85 | ✗ 错误: check_translation.py 加载失败 | ✗ Error: check_translation.py failed to load |
| 93 | 正在复制 table.json... | Copying table.json... |
| 100 | ✗ 错误: table.json 不存在 | ✗ Error: table.json not found |
| 105 | ⚠ 目标文件已存在 | ⚠ Target file exists |
| 106 | 是否覆盖? (y/n): | Overwrite? (y/n): |
| 109 | 已取消 | Cancelled |
| 121 | ✓ 已复制到 | ✓ Copied to |
| 124 | ✗ 复制失败 | ✗ Copy failed |
| 127 | 正在杀死进程... | Killing process... |
| 131 | ✓ 进程已终止 | ✓ Process terminated |
| 136 | 状态检查: | Status Check: |
| 140-162 | 各项状态检查 | Status check items |
| 175 | 翻译质量检查工具 | Translation Quality Check Tool |
| 180-185 | 菜单选项 1-9, 0 | Menu options 1-9, 0 |
| 187 | 请选择: | Please select: |
| 196-199 | 按回车继续... | Press Enter to continue... |
| 201 | 无效选择 | Invalid selection |

### 修改位置 / Modification Location
- File: `start.sh`
- Lines: ~203 lines (full rewrite of Chinese to English)

---

## Part 2: 界面多语言支持 / Frontend Multilingual Support

### 方案设计 / Design

采用**单模板多语言方案** (Single template with multilingual):

1. **语言存储**: 存储在数据库 `groq_config` 表中 / Store in database `groq_config` table
2. **默认语言**: 英语 (en) / Default: English (en)
3. **语言切换**: 设置页面下拉框 / Language switch in settings page

```javascript
// 方式 1: 从数据库获取语言设置
async function loadLanguageSetting() {
    const resp = await fetch('/api/groq/status');
    const data = await resp.json();
    return data.language || 'en';
}

// 方式 2: 通过 API 设置语言
async function setLanguageSetting(lang) {
    await fetch('/api/groq/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({language: lang, ...})
    });
}
```

### 数据库修改

```sql
-- 添加 language 字段到 groq_config 表
ALTER TABLE groq_config ADD COLUMN language TEXT DEFAULT 'en';
```

### 后端 API 修改

```python
# /api/groq/status 返回 language
elif self.path == '/api/groq/status':
    api_config = TRANSLATION_APIS.get("groq", {})
    self.send_json({
        ...
        "language": api_config.get("language", "en")
    })

# 新增 /api/language 接口
elif self.path == '/api/language':
    action = data.get("action")
    if action == "get":
        self.send_json({"language": current_language})
    elif action == "set":
        language = data.get("language", "en")
        # 保存到数据库
        ...
```

### 语言切换位置 / Language Switch Location

在**设置页面** (`settings.html`) 标题下方添加语言切换下拉框：

```html
<div class="config-row">
    <label>Language:</label>
    <select id="lang-switch" onchange="setLanguage(this.value)">
        <option value="en">English</option>
        <option value="zh">简体中文</option>
    </select>
</div>
```

### 前端需要修改的��符串 / Strings to Modify

| Key | English | 简体中文 |
|-----|---------|----------|
| title | Translation Quality Check Tool | 翻译质量检查工具 |
| sync_jp | Sync Original | 同步原文 |
| sync_cn | Sync Translation | 同步翻译 |
| settings | Settings | 设置 |
| tutorial | Tutorial | 查看教程 |
| warning | Note: Sync extracts content... | 注意：同步即从原文件... |
| jump | Jump | 跳转 |
| search | Search | 搜索 |
| filter | Filter | 过滤 |
| show_fixed | Show Confirmed | 显示已确认 |
| too_long | Translation too long | 翻译过长 |
| confirm | Confirm | 确认 |
| original | Original | 原文 |
| current_cn | Current Translation | 当前翻译 |
| ai_suggestion | AI Suggestion | AI建议 |
| refresh | Refresh | 刷新 |
| copy | Copy | 复制 |
| editor | Editor | 编辑区 |
| char_count | Characters | 字数 |
| save_next | Save & Next | 保存→跳转 |
| prev | Previous | 上一条 |
| next | Next | 下一条 |
| loading | Loading... | 加载中... |
| empty | (Empty) | (空) |
| no_original | (No original) | (无原文) |

### 受影响文件 / Affected Files

| File | Changes |
|------|--------|
| `templates/index.html` | Add i18n, replace ~40 static strings |
| `templates/settings.html` | Add language switch dropdown, replace ~20 strings |
| `templates/tutorial.html` | Replace Chinese strings |

### 需要新增的功能 / New Features

1. **数据库字段**: language 字段在 groq_config 表
2. **后端 API**: /api/language GET/SET 接口
3. **语言切换下拉框**: settings.html 中
4. **i18n 映射**: 单模板多语言支持

---

## 执行顺序 / Execution Order

### 阶段 1: start.sh 英语化
1. Replace all Chinese prompts with English equivalents
2. Test the script

### 阶段 2: 数据库修改
1. Add `language` column to `groq_config` table
2. Add language field to load_groq_config() and save_groq_config()

### 阶段 3: 后端 API
1. Add `/api/language` GET/SET interface
2. Modify `/api/groq/status` to return language

### 阶段 4: 前端多语言支持
1. Create i18n mapping object in JavaScript
2. Replace static text with `t()` function calls in index.html
3. Add language switch dropdown in settings.html
4. Replace static text in settings.html and tutorial.html
5. Test language switching

---

## 文件修改清单 / File Modification List

| File | Type | Lines | Description |
|------|------|-------|-------------|
| start.sh | Modify | ~50 | All Chinese to English |
| check_translation.py | Modify | ~30 | Add language column, /api/language |
| templates/index.html | Modify | ~100 | i18n, replace strings |
| templates/settings.html | Modify | ~50 | Language dropdown, strings |
| templates/tutorial.html | Modify | ~30 | Replace Chinese strings |

---

## 待确认 / To Confirm

~~1. **默认语言**: 英语还是简体中文？ / Default language: English or Chinese?~~
~~2. **语言选择存储**: localStorage 还是 session？ / Storage: localStorage or session?~~
~~3. **是否需要 separate 中文版本**: 如 index_zh.html？ / Need separate Chinese version?~~

**方案已确认**:
1. **默认语言**: 英语 (en) - 已确认
2. **语言存储**: 数据库 (groq_config 表) - 已确认
3. **单模板多语言**: 使用 i18n 映射 - 已确认

---

## 预计工作量 / Estimated Work

| Task | Lines |
|------|-------|
| start.sh English | ~50 |
| Frontend i18n | ~100 |
| Testing | ~20 |
| **Total** | ~170 lines |
