# 第四轮性能优化计划文档

## 审查日期
2026-04-17

## 优化范围
- 后端: check_translation.py
- 前端: templates/index.html

---

## 一、API 性能优化

### 1.1 /api/update 增量更新
**位置**: do_POST /api/update 处理 (第262-280行)
**问题**: 每次更新都读取整个 JSON 文件、修改后写入全量文件
**影响**: 数据量大的情况下性能差
**方案**: 改为仅更新 SQLite，延迟同步或使用流式写入

**优化后**:
```python
elif self.path == '/api/update':
    # 仅更新 SQLite，不操作 table.json
    file_key = data.get("file")
    idx = data.get("index")
    new_cn = data.get("cn", "")
    # ... SQLite 更新逻辑
```

### 1.2 /api/all 分页支持
**位置**: do_GET /api/all (第181-182行)
**问题**: 一次性返回全部数据，数据量大时会卡死
**方案**: 添加分页参数

**API 设计**:
- `GET /api/all` - 返回第一页 (默认100条)
- `GET /api/all?page=2&size=50` - 返回第2页，每页50条

### 1.3 /api/next 缓存优化
**位置**: do_GET /api/next (第198-217行)
**问题**: 每次请求都执行 SQL
**方案**: 添加简单缓存机制（内存缓存10秒）

---

## 二、前端渲染优化

### 2.1 列表虚拟滚动
**位置**: renderList 函数 (第202-217行)
**问题**: 渲染大量列表项时 DOM 节点过多
**方案**: 实现虚拟滚动，只渲染可视区域内的项

### 2.2 防抖渲染更新
**位置**: renderItem 函数
**问题**: 连续快速调用 renderItem 会导致重复渲染
**方案**: 添加 debounce

### 2.3 图片懒加载 (如有)
**方案**: 使用 IntersectionObserver

---

## 三、数据库优化

### 3.1 添加索引
**位置**: init_db 函数
**问题**: 搜索和过滤查询无索引
**方案**: 添加复合索引

```sql
CREATE INDEX IF NOT EXISTS idx_search ON translation_status(is_fixed, file_key);
CREATE INDEX IF NOT EXISTS idx_filter ON translation_status(is_fixed, LENGTH(cn) - LENGTH(jp));
```

### 3.2 连接池
**位置**: 数据库连接
**问题**: 每次请求都创建新连接
**方案**: 使用连接池或长连接

---

## 四、执行计划

### 阶段一：API 优化 (3项)
1. /api/update 增量更新（仅写 SQLite）
2. /api/all 分页支持
3. /api/next 缓存优化

### 阶段二：前端优化 (3项)
1. 列表虚拟滚动
2. 防抖渲染更新
3. 图片懒加载

### 阶段三：数据库优化 (2项)
1. 添加索引
2. 连接池

---

## 五、预计改动量

| 阶段 | 任务数 | 预计改动行数 |
|------|--------|-------------|
| API 优化 | 3 | 约60行 |
| 前端优化 | 3 | 约80行 |
| 数据库优化 | 2 | 约30行 |
| **总计** | **8** | **约170行** |

---

## 六、风险提示

1. /api/update 移除 table.json 写入需确保定时同步机制
2. 虚拟滚动实现复杂度较高，建议使用轻量方案
3. 缓存需考虑数据一致性
