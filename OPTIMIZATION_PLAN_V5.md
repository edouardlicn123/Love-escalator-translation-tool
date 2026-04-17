# 第五轮代码优化计划文档

## 审查日期
2026-04-17

## 优化范围
- 后端: check_translation.py
- 前端: templates/index.html

---

## 一、后端优化计划

### 1.1 删除冗余函数调用
**位置**: check_translation.py 第385行
**问题**: `/api/update` 接口调用 `load_data()` 但未使用返回值
**当前代码**:
```python
elif self.path == '/api/update':
    full_data = load_data()  # <-- 冗余，未使用
    file_key = data.get("file")
    ...
```
**方案**: 删除 `full_data = load_data()` 这一行

### 1.2 移动 import 语句
**位置**: check_translation.py 第314行
**问题**: `import time` 在函数内导入
**方案**: 移至文件顶部 (import 区域)

### 1.3 缓存清理
**位置**: check_translation.py /api/update 处理
**问题**: 更新数据后未清理缓存，导致返回旧数据
**方案**: 更新后清除 cache 字典中 `/api/next` 相关缓存

---

## 二、前端优化计划

### 2.1 修复 textarea XSS 漏洞
**位置**: index.html 第457行
**问题**: textarea 内容 `${currentCn}` 未转义
**当前代码**:
```html
<textarea id="editor-textarea" rows="3" oninput="updateCharCount()">${currentCn}</textarea>
```
**方案**: 改为 `${escapeHtml(currentCn)}`

### 2.2 删除未使用变量
**位置**: index.html 第157行
**问题**: `renderDebounceTimer` 在 state 中定义但未使用
**方案**: 从 state 中删除

### 2.3 删除未使用函数
**位置**: index.html 第168行
**问题**: `debouncedRenderItem` 定义但未使用
**方案**: 删除该定义

### 2.4 使用 fetchWithTimeout
**位置**: index.html 关键 API 调用
**问题**: `fetchWithTimeout` 定义但未使用
**方案**: 将 `loadAISuggestion` 中的 fetch 改为使用 fetchWithTimeout

---

## 三、执行计划

### 阶段一：后端优化 (3项)
1. 删除冗余 load_data() 调用
2. 移动 import time 到顶部
3. 添加缓存清理逻辑

### 阶段二：前端优化 (4项)
1. 修复 textarea XSS 漏洞
2. 删除未使用变量
3. 删除未使用函数
4. 使用 fetchWithTimeout

---

## 四、预计改动量

| 阶段 | 任务数 | 预计改动行数 |
|------|--------|-------------|
| 后端优化 | 3 | 约15行 |
| 前端优化 | 4 | 约20行 |
| **总计** | **7** | **约35行** |
