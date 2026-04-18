# 翻译同步计划

## 问题说明

当前系统有两份数据：

| 数据源 | 用途 | 状态 |
|--------|------|------|
| table.json | 原始翻译文本（jp + 初始 cn） | 只读 |
| translation_status.db | 用户修改后的翻译 | 可读写 |

**用户保存翻译时**：
- 只更新 `translation_status.db` 的 `cn` 字段
- `table.json` 保持不变

**问题**：用户期望修改翻译后 `table.json` 也同步更新。

---

## 解决方案

在 `/api/update` 时同时更新 `table.json`

### 修改位置
**文件**: check_translation.py  
**函数**: do_POST `/api/update` 处理

### 修改逻辑
```python
# 1. 更新数据库（已有）
conn.execute("UPDATE translation_status SET cn=?, ... WHERE file_key=? AND index_id=?", ...)

# 2. 同时更新 table.json
with open(config.data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
if file_key in data and index_id < len(data[file_key]):
    data[file_key][index_id]['cn'] = new_cn
    with open(config.data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### 注意事项
- 需要处理 JSON 写入失败的情况
- 可能需要添加错误回滚机制

---

## 预计改动
约 15 行代码
