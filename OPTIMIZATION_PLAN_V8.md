# 第八轮代码优化计划文档

## 审查日期
2026-04-17

## 优化范围
- 后端: check_translation.py
- 前端: templates/index.html

---

## 一、后端优化计划

### 1.1 删除废弃注释
**位置**: check_translation.py 第62行
**问题**: `# SYSTEM_TITLE 已废弃，使用 config.system_title` 注释冗余
**方案**: 删除该注释

### 1.2 添加分页参数错误处理
**位置**: check_translation.py 第305-306行
**问题**: page/size 解析可能抛出 ValueError 导致服务崩溃
**方案**: 添加 try-except 保护

---

## 二、前端优化计划

### 2.1 移除未使用变量
**位置**: index.html state 对象
**问题**: `searchDebounceTimer` 在 nextSearch 中未使用
**方案**: 删除 searchDebounceTimer 相关代码

---

## 三、执行计划

### 阶段一：后端优化 (2项)
1. 删除废弃注释
2. 添加分页参数错误处理

### 阶段二：前端优化 (1项)
1. 移除未使用变量

---

## 四、预计改动量

| 阶段 | 任务数 | 预计改动行数 |
|------|--------|-------------|
| 后端优化 | 2 | 约10行 |
| 前端优化 | 1 | 约5行 |
| **总计** | **3** | **约15行** |
