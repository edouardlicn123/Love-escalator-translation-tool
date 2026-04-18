# 多语言支持计划

## 目标

1. **start.sh**: 全部内容改为英语
2. **界面**: 默认为英语，可选择简体中文

---

## Part 1: start.sh 英语化

### 当前状态
- 所有提示和菜单为中文
- 需要全部改为英文

### 修改清单

| 行号 | 当前中文 | 修改为英文 |
|------|----------|-------------|
| 2 | 翻译质量检查工具 - 启动脚本 | Translation Quality Check Tool - Startup Script |
| 31 | 正在安装依赖... | Installing dependencies... |
| 36 | ✓ requests, pysocks 已安装 | ✓ requests, pysocks installed |
| 38 | ✓ 依赖已安装 | ✓ Dependencies installed |
| 43 | 正在初始化数据库... | Initializing database... |
| 46 | ✗ 错误: table.json 不存在 | ✗ Error: table.json not found |
| 59 | ✓ 插入: {n} 条 | ✓ Inserted: {n} entries |
| 60 | ✓ 更新: {n} 条 | ✓ Updated: {n} entries |
| 65 | 正在启动服务器... | Starting server... |
| 68 | ⚠ 警告: requests 未安装，请先运行选项2安装依赖 | ⚠ Warning: requests not installed, run option 2 first |
| 74 | ✗ 错误: sqlite3 不可用 | ✗ Error: sqlite3 not available |
| 79 | ✗ 错误: table.json 不存在，无法加载翻译数据 | ✗ Error: table.json not found, cannot load data |
| 85 | ✗ 错误: check_translation.py 加载失败 | ✗ Error: check_translation.py failed to load |
| 93 | 正在复制 table.json... | Copying table.json... |
| 100 | ✗ 错误: table.json 不存在 | ✗ Error: table.json not found |
| 105 | ⚠ 目标文件已存在: {path} | ⚠ Target file exists: {path} |
| 106 | 是否覆盖? (y/n): | Overwrite? (y/n): |
| 109 | 已取消 | Cancelled |
| 121 | ✓ 已复制到 {path} | ✓ Copied to {path} |
| 124 | ✗ 复制失败 | ✗ Copy failed |
| 127 | 正在杀死进程... | Killing process... |
| 131 | ✓ 进程已终止 | ✓ Process terminated |
| 136 | 状态检查: | Status Check: |
| 140 | requests: ✓ 已安装 | requests: ✓ Installed |
| 142 | requests: ✗ 未安装 | requests: ✗ Not installed |
| 146 | sqlite3: ✓ 可用 | sqlite3: ✓ Available |
| 148 | sqlite3: ✗ 不可用 | sqlite3: ✗ Not available |
| 152 | table.json: ✓ 存在 | table.json: ✓ Exists |
| 154 | table.json: ✗ 不存在 | table.json: ✗ Not found |
| 160 | 数据库: ✓ 已建立 ({n} 条, {m} 条已修复) | Database: ✓ Established ({n} entries, {m} fixed) |
| 162 | 数据库: ✗ 未建立 | Database: ✗ Not established |
| 166 | 代理: ✓ 已启用 | Proxy: ✓ Enabled |
| 168 | 代理: ✗ 未启用 | Proxy: ✗ Not enabled |
| 175 | 翻译质量检查工具 | Translation Quality Check Tool |
| 180 | 1. 启动服务 | 1. Start Server |
| 181 | 2. 安装依赖 | 2. Install Dependencies |
| 182 | 3. 初始化数据库 | 3. Initialize Database |
| 183 | 4. 传输翻译文件 | 4. Transfer Translation File |
| 184 | 9. 杀死进程 | 9. Kill Process |
| 185 | 0. 退出 | 0. Exit |
| 187 | 请选择: | Please select: |
| 196 | 按回车继续... | Press Enter to continue... |
| 197 | 按回车继续... | Press Enter to continue... |
| 198 | 按回车继续... | Press Enter to continue... |
| 199 | 按回车继续... | Press Enter to continue... |
| 201 | 无效选择 | Invalid selection |

### 预计改动
- ~50 行注释和提示文本
- ~5 行菜单项

---

## Part 2: 界面多语言支持

### 方案设计

**方案 A**: 单一的国际化字符串替换（推荐）
- 创建语言映射对象
- 界面加载时根据设置选择语言
- 存储在 localStorage

**方案 B**: 独立的中英文版本
- 创建 `index_en.html` 和 `index_zh.html`
- 通过 URL 参数选择

### 推荐方案

采用 **方案 A**，在 `index.html` 中添加语言切换功能

### 实现结构

```javascript
// 语言映射
const i18n = {
    en: {
        title: "Translation Quality Check Tool",
        sync_jp: "Sync Original",
        sync_cn: "Sync Translation",
        settings: "Settings",
        tutorial: "Tutorial",
        warning: "Note: Sync extracts content from source file...",
        jump: "Jump",
        search: "Search",
        filter: "Filter",
        show_fixed: "Show Confirmed",
        too_long: "Translation too long",
        confirm: "Confirm",
        original: "Original",
        current_cn: "Current Translation",
        ai_suggestion: "AI Suggestion",
        refresh: "Refresh",
        copy: "Copy",
        editor: "Editor",
        char_count: "Characters",
        save_next: "Save & Next",
        prev: "Previous",
        next: "Next"
    },
    zh: {
        title: "翻译质量检查工具",
        sync_jp: "同步原文",
        sync_cn: "同步翻译",
        settings: "设置",
        tutorial: "查看教程",
        warning: "注意：同步即从原文件里重新提取内容...",
        jump: "跳转",
        search: "搜索",
        filter: "过滤",
        show_fixed: "显示已确认",
        too_long: "翻译过长",
        confirm: "确认",
        original: "原文",
        current_cn: "当前翻译",
        ai_suggestion: "AI建议",
        refresh: "刷新",
        copy: "复制",
        editor: "编辑区",
        char_count: "字数",
        save_next: "保存→跳转",
        prev: "上一条",
        next: "下一条"
    }
};

// 当前语言
let currentLang = localStorage.getItem('lang') || 'en';

// 翻译函数
function t(key) {
    return i18n[currentLang][key] || i18n['en'][key];
}

// 语言切换函数
function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    renderUI();
}
```

### 前端需要修改的字符串

| 位置 | 英文 | 简体中文 |
|------|------|----------|
| h1 标题 | Translation Quality Check Tool | 翻译质量检查工具 |
| 同步原文按钮 | Sync Original | 同步原文 |
| 同步翻译按钮 | Sync Translation | 同步翻译 |
| 设置链接 | Settings | 设置 |
| 教程链接 | Tutorial | 查看教程 |
| 警告提示 | Note: Sync extracts content... | 注意：同步即从原文件... |
| 跳转 | Jump | 跳转 |
| 搜索 | Search | 搜索 |
| 过滤 | Filter | 过滤 |
| 显示已确认 | Show Confirmed | 显示已确认 |
| 翻译过长 | Translation too long | 翻译过长 |
| 确认 | Confirm | 确认 |
| ID | ID | ID |
| 原文 | Original | 原文 |
| 当前翻译 | Current Translation | 当前翻译 |
| AI建议 | AI Suggestion | AI建议 |
| 刷新 | Refresh | 刷新 |
| 复制 | Copy | 复制 |
| 编辑区 | Editor | 编辑区 |
| 字数 | Characters | 字数 |
| 保存→跳转 | Save & Next | 保存→跳转 |
| 上一条 | Previous | 上一条 |
| 下一条 | Next | 下一条 |
| 加载中 | Loading... | 加载中... |
| 空 | (Empty) | (空) |
| 无原文 | (No original) | (无原文) |

### 语言切换 UI

在标题附近添加语言切换下拉框：

```html
<select id="lang-switch" onchange="setLanguage(this.value)" style="margin-left:20px;">
    <option value="en" ${currentLang==='en'?'selected':''}>English</option>
    <option value="zh" ${currentLang==='zh'?'selected':''}>简体中文</option>
</select>
```

### 预计改动
- ~60 行 JavaScript (i18n 对象)
- ~40 个 HTML 字符串替换
- ~5 行语言切换 UI

---

## 执行顺序

### ���段 1: start.sh 英语化
1. 使用英文替换所有中文提示
2. 测试运行

### 阶段 2: 前端多语言支持
1. 创建 i18n 映射对象
2. 替换静态文本为函数调用
3. 添加语言切换下拉框
4. 测试功能

---

## 文件修改清单

| 文件 | 改动 | 预计行数 |
|------|------|----------|
| start.sh | 注释+提示 | ~50 行 |
| index.html | 添加 i18n + 文本替换 | ~100 行 |

---

## 待确认

1. 默认语言选择：英语还是简体中文？
2. 语言选择是否需要 remember？（localStorage）
3. 是否需要 separate 中文界面文件？（如 index_zh.html）
