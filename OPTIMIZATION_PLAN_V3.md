# 第三轮代码优化计划文档

## 审查日期
2026-04-17

## 优化范围
- 后端: check_translation.py
- 前端: templates/index.html

---

## 一、严重问题 (需立即修复)

### 1.1 后端函数缺失
**位置**: check_translation.py 第262、271行
**问题**: `load_data()` 和 `save_data()` 函数缺失，但被 `/api/update` 接口调用
**影响**: 保存翻译功能会报错
**方案**: 重新添加这两个函数

```python
def load_data(): 
    with open(config.data_file, encoding='utf-8') as f:
        return json.load(f)

def save_data(data): 
    with open(config.data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 二、后端优化计划

### 2.1 添加 Timeout 异常处理
**位置**: translate_with_api 函数 (第129行附近)
**问题**: 缺少 `requests.exceptions.Timeout` 单独处理
**方案**: 添加 Timeout 异常捕获

### 2.2 简化三元表达式
**位置**: 第120行
**问题**: `use_proxy if use_proxy is not None else config.use_proxy` 嵌套复杂
**方案**: 简化为：
```python
proxy_setting = config.use_proxy if use_proxy is None else use_proxy
```

### 2.3 重构 API 路由
**位置**: Handler 类的 do_GET 和 do_POST 方法
**问题**: 方法过长（各约80行），不易维护
**方案**: 将各路由处理提取为独立方法

**重构后结构**:
```
Handler 类
├── do_GET()
│   ├── handle_root()           # /
│   ├── handle_settings()      # /settings.html
│   ├── handle_tutorial()       # /tutorial.html
│   ├── handle_api_all()        # /api/all
│   ├── handle_api_models()     # /api/models
│   ├── handle_api_apis()       # /api/translation-apis
│   ├── handle_api_db_stats()   # /api/db/stats
│   ├── handle_api_groq_status()# /api/groq/status
│   ├── handle_api_proxy_status()# /api/proxy/status
│   ├── handle_api_next()       # /api/next
│   └── handle_api_search()     # /api/search
│
└── do_POST()
    ├── handle_db_init()        # /api/db/init
    ├── handle_db_backup()      # /api/db/backup
    ├── handle_filter()         # /api/filter
    ├── handle_update()         # /api/update
    ├── handle_translate()      # /api/translate
    ├── handle_groq_config()    # /api/groq/config
    └── handle_proxy_config()   # /api/proxy/config
```

---

## 三、前端优化计划

### 3.1 修复 XSS 漏洞 (两处)

**位置**: 第415行 `currentCn`
**问题**: `<div class="option-content" id="current-cn">${currentCn || '(空)'}</div>` 未转义
**方案**: 改为 `${escapeHtml(currentCn) || '(空)'}`

**位置**: 第208行 `jpShort`
**问题**: `<div class="col-jp">${jpShort}</div>` 未转义
**方案**: 改为 `${escapeHtml(jpShort)}`

### 3.2 修复语法错误
**位置**: 第381-390行 backupDb 函数
**问题**: 缺少右花括号 `}`
**当前代码**:
```javascript
async function backupDb() {
    try {
        const resp = await fetch('/api/db/backup', {method: 'POST'});
        const data = await resp.json();
        if (data.success) {
            alert('备份成功: ' + data.path);
    } else {  // <-- 缺少 { 
        alert('备份失败: ' + data.error);
    }  // <-- 缺少 }
}
```
**方案**: 补全为：
```javascript
async function backupDb() {
    try {
        const resp = await fetch('/api/db/backup', {method: 'POST'});
        const data = await resp.json();
        if (data.success) {
            alert('备份成功: ' + data.path);
        } else {
            alert('备份失败: ' + data.error);
        }
    }
}
```

### 3.3 修复缩进错误
**位置**: 第482行 saveAndReload
**问题**: 缩进为2空格而非4空格
**当前**: `async function saveAndReload(cn) {` 前有多余空格
**方案**: 修正为统一4空格缩进

### 3.4 添加请求超时
**位置**: 全局 fetch 调用
**问题**: 无请求超时处理，可能导致请求卡死
**方案**: 添加通用 fetchWithTimeout 函数

```javascript
async function fetchWithTimeout(url, options = {}, timeout = 5000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const resp = await fetch(url, {...options, signal: controller.signal});
        clearTimeout(id);
        return resp;
    } catch (e) {
        clearTimeout(id);
        if (e.name === 'AbortError') {
            throw new Error('请求超时');
        }
        throw e;
    }
}
```

### 3.5 统一搜索防抖
**位置**: 第558行 doSearch
**问题**: 直接调用无防抖，与 nextSearch 不一致
**方案**: 保持 doSearch 直接调用（搜索按钮已有点击防抖），但统一使用 debouncedSearch

---

## 四、执行计划

### 阶段一：修复严重问题 (1项)
1. 添加 load_data() 和 save_data() 函数

### 阶段二：后端优化 (3项)
1. 添加 Timeout 异常处理
2. 简化三元表达式
3. 重构 API 路由

### 阶段三：前端优化 (5项)
1. 修复 XSS 漏洞 (两处)
2. 修复语法错误
3. 修复缩进错误
4. 添加请求超时
5. 统一搜索防抖

---

## 五、预计改动量

| 阶段 | 任务数 | 预计改动行数 |
|------|--------|-------------|
| 严重问题 | 1 | 约15行 |
| 后端优化 | 3 | 约100行 (主要是重构) |
| 前端优化 | 5 | 约40行 |
| **总计** | **9** | **约155行** |
