# 开发指南

## 核心原则

### 1. 尽量减少服务器重启
- 修改 Python 代码后等待用户测试，不主动启动服务端验证
- 修改 HTML/JS 后由用户在浏览器刷新测试
- 只在明显语法错误时才运行 `python3 -m py_compile` 验证

### 2. 节约 Token
- 避免反复测试 API 调用
- 对代码修改有 80% 把握即可执行
- 用户反馈问题再进行针对性修复

## 项目结构

```
Love-escalator-translation-tool/
├── check_translation.py    # 后端服务 (端口 5382)
├── templates/
│   └── index.html       # 前端页面
├── table.json           # 翻译数据源
├── translation_status.db # SQLite 数据库
└── AGENTS.md           # 本文件
```

## 数据库设计

### translation_status 表

| 字段 | 说明 |
|------|------|
| id | 主键 (自增) |
| file_key | 文件名 |
| index_id | 索引 |
| jp | 日文原文 |
| cn | 中文翻译 |
| is_translated | 是否有翻译 (0/1) |
| is_fixed | 是否已确认 (0/1) |
| issue_type | 问题类型 |
| ai_suggestion | AI建议 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## API 接口

### GET
- `/` - 首页 HTML
- `/api/next` - 获取所有 is_fixed=0 的记录
- `/api/db/stats` - 数据库统计
- `/api/groq/status` - Groq API 状态
- `/api/proxy/status` - 代理状态

### POST
- `/api/db/init` - 初始化数据库 (sync_db)
- `/api/db/backup` - 备份数据库
- `/api/update` - 更新翻译 (file, index, cn)
- `/api/groq/config` - 保存 Groq 配置 (apiKey, model, targetLang)
- `/api/proxy/config` - 保存代理配置 (enabled)
- `/api/translate` - AI 翻译 (text, targetLang, useProxy)
- `/api/filter` - 过滤问题 (已废弃)

## 启动方式

```bash
python3 check_translation.py --port 5382
```

### 服务器重启步骤

1. **强制杀死旧进程** (确保完全杀掉)
   ```bash
   pkill -9 -f "check_translation.py" 2>/dev/null
   fuser -k 5382/tcp 2>/dev/null
   sleep 2
   ```

2. **启动新进程**
   ```bash
   nohup python3 check_translation.py --port 5382 > /tmp/server.log 2>&1 &
   sleep 3
   ```

3. **验证服务正常** (必须步骤!)
   ```bash
   curl -s "http://127.0.0.1:5382/api/db/stats"
   ```
   - 如果返回正常 JSON → 启动成功
   - 如果返回错误 → 检查 `/tmp/server.log`

### 后端路径匹配规则

- 使用 `startswith()` 匹配带 query string 的路径
- **错误**：`if self.path == '/api/next':` （无法匹配 `/api/next?show_fixed=1`）
- **正确**：`if self.path.startswith('/api/next'):`

## 数据字段含义

| 字段 | 触发条件 |
|------|----------|
| is_translated | 初始化时：有 cn 内容 → 1，无 → 0 |
| is_fixed | 初始化 = 0，点保存跳转 → 1 |

## 注意事项

### 1. 浏览器缓存
- 修改 HTML 后用户需强制刷新 (Ctrl+F5)
- 或使用私域窗口测试
- 服务器端和 HTML 已添加防止缓存的 HTTP 头，刷新即可

### 2. 数据库同步
- 修改 table.json 后运行 `/api/db/init` 重新同步

### 3. 搜索功能
- `/api/search?keyword=关键词` 返回匹配结果

## 常见问题

1. **页面不更新** → 清除浏览器缓存或私域窗口
2. **翻译失败** → 检查代理设置
3. **API Key 提示未填写** → 在设置中填写并保存