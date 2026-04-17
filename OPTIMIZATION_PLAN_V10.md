# 第十轮代码优化计划文档

## 问题描述
AI 翻译时会丢失原文中的换行符 `\n`。

**原因**: AI 模型可能会忽略或简化换行符。

**示例**:
- 原文: `\n 《又过了10分钟》`
- AI 翻译: `《又过了10分钟》` (丢失 `\n`)

---

## 解决方案

在发送给 AI 翻译之前，将换行符替换为特殊占位符（如 `{{NEWLINE}}`），AI 翻译完成后，再将占位符替换回换行符。

---

## 修改计划

### 修改位置
**文件**: check_translation.py
**函数**: translate_with_api (第174行附近)

### 具体修改
在 payload 构建时，替换换行符：
```python
# 发送前：替换 \n 为占位符
text_for_translate = text.replace('\n', '{{NEWLINE}}')

# AI 返回后：还原 \n
content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
translation = content.replace('{{NEWLINE}}', '\n') if content else ""
```

---

## 预计改动
约 4 行代码修改

---

## 待确认
是否需要对前端也做相应处理？（前端显示时应自动正确处理）
