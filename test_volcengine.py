#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
import sys

API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
API_KEY = "你的API_KEY"  # 请替换

payload = {
    "model": "doubao-pro-32k",
    "messages": [
        {"role": "system", "content": "You are a professional translator. Translate the following Japanese text to Chinese. Only return the translation, no explanations."},
        {"role": "user", "content": "你好"}
    ],
    "stream": False
}

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + API_KEY
}

print("=" * 50)
print("火山引擎 API 测试")
print("=" * 50)
print("URL:", API_URL)
print("=" * 50)

try:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    print("\n发送请求...")
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("响应状态:", resp.status)
        response_body = resp.read().decode('utf-8')
        print("响应体:", response_body[:500])
        
        result = json.loads(response_body)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("\n翻译结果:", content)

except urllib.error.HTTPError as e:
    print("\nHTTP错误:", e.code)
    print("错误信息:", e.read().decode('utf-8'))
except Exception as e:
    print("\n错误:", type(e).__name__, str(e))

print("=" * 50)
