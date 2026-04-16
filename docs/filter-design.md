# 过滤功能设计文档

## 需求概述

在搜索栏下方添加过滤选项，允许用户排除已翻译或已确认的记录。

## UI 设计

```
┌─────────────────┐
│ 跳转            │
│ [输入框] [按钮] │
├─────────────────┤
│ 搜索            │
│ [输入框] [按钮] │
├─────────────────┤
│ 过滤            │
│ ☑ 排除已翻译    │
│ ☑ 排除已确认    │
└─────────────────┘
```

## 数据字段含义

| 字段 | 值 | 说明 |
|------|-----|------|
| is_translated | 0 | 未翻译 |
| is_translated | 1 | 已翻译 |
| is_fixed | 0 | 未确认 |
| is_fixed | 1 | 已确认 |

## 过滤逻辑

| 复选框 | 条件 |
|--------|------|
| 排除已翻译 | is_translated = 0 |
| 排除已确认 | is_fixed = 0 |

两者可同时启用，组合条件为 `is_translated = 0 AND is_fixed = 0`

## API 设计

### GET /api/next

**参数** (URL query):
- `exclude_translated`: 1 表示排除已翻译
- `exclude_fixed`: 1 表示排除已确认

**示例**:
```
/api/next?exclude_translated=1&exclude_fixed=1
```

### GET /api/search

**参数** (URL query):
- `keyword`: 搜索关键词
- `type`: all/jp/cn
- `exclude_translated`: 1 表示排除已翻译
- `exclude_fixed`: 1 表示排除已确认

**示例**:
```
/api/search?keyword=测试&type=all&exclude_fixed=1
```

## 实现清单

1. **HTML**: 在搜索框下方添加过滤区域
2. **CSS**: 添加过滤复选框样式
3. **JS**: 
   - 添加过滤状态变量
   - 修改 loadIssues() 函数支持过滤参数
   - 保存/恢复过滤状态到 localStorage
4. **后端**: 
   - 修改 `/api/next` 支持过滤参数
   - 修改 `/api/search` 支持过滤参数

## 文件修改

- `templates/index.html` - 前端 UI 和逻辑
- `check_translation.py` - 后端 API