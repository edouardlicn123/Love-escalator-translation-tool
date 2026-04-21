#!/bin/bash
# Groq API 测试脚本（支持代理）
# 用法: ./test_groq.sh [API_KEY] [模型]

API_KEY="${1}"
MODEL="${2:-llama-3.1-8b-instant}"

# 启用代理（如果 bashrc 中有配置）
if grep -q "proxy_on" ~/.bashrc 2>/dev/null; then
    export http_proxy="http://127.0.0.1:10808"
    export https_proxy="http://127.0.0.1:10808"
    export all_proxy="socks5://127.0.0.1:10808"
fi

if [ -z "$API_KEY" ]; then
    echo "用法: $0 <API_KEY> [模型]"
    exit 1
fi

echo "测试 Groq API..."
RESPONSE=$(curl -s -X POST "https://api.groq.com/openai/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}],\"stream\":false}")

echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])" 2>/dev/null || echo "$RESPONSE"
