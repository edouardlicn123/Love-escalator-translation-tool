#!/bin/bash
# 翻译质量检查工具 - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 配置文件
CONFIG_FILE="$SCRIPT_DIR/config.json"

# 读取配置
if [ -f "$CONFIG_FILE" ]; then
    PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['port'])" 2>/dev/null)
    TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('hf_token', ''))" 2>/dev/null)
fi

PORT=${PORT:-5000}

echo "========================================"
echo "   翻译质量检查工具"
echo "========================================"
echo "访问地址: http://localhost:$PORT"
echo "配置文件: $CONFIG_FILE"
echo "========================================"

# 启动服务器
exec python3 check_translation.py --port $PORT