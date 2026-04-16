#!/bin/bash
# 翻译质量检查工具 - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="$SCRIPT_DIR/config.json"
DB_FILE="$SCRIPT_DIR/translation_status.db"
DATA_FILE="$SCRIPT_DIR/table.json"
VENV_DIR="$SCRIPT_DIR/venv"

PORT=5382

check_proxy() {
    if [ -n "$http_proxy" ] || [ -n "$https_proxy" ]; then
        return 0
    fi
    if grep -q "proxy_on" ~/.bashrc 2>/dev/null; then
        return 1
    fi
    return 1
}

enable_proxy() {
    export http_proxy="http://127.0.0.1:10808"
    export https_proxy="http://127.0.0.1:10808"
    export all_proxy="socks5://127.0.0.1:10808"
}

install_deps() {
    echo "正在安装依赖..."
    
    if ! python3 -c "import requests" 2>/dev/null; then
        python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null
        pip3 install requests pysocks --break-system-packages 2>/dev/null
        echo "✓ requests, pysocks 已安装"
    else
        echo "✓ 依赖已安装"
    fi
}

init_db() {
    echo "正在初始化数据库..."
    
    if [ ! -f "$DATA_FILE" ]; then
        echo "✗ 错误: table.json 不存在"
        return 1
    fi
    
    python3 -c "
import sys
sys.path.insert(0, '.')
import check_translation
check_translation.DATA_FILE = '$DATA_FILE'
check_translation.DB_FILE = '$DB_FILE'
check_translation.CONFIG_FILE = '$CONFIG_FILE'
check_translation.load_config()
result = check_translation.sync_db()
print(f'✓ 插入: {result[\"inserted\"]} 条')
print(f'✓ 更新: {result[\"updated\"]} 条')
"
}

start_server() {
    echo "正在启动服务器..."
    
    if ! python3 -c "import requests" 2>/dev/null; then
        echo "⚠ 警告: requests 未安装，请先运行选项2安装依赖"
        read -p "继续? (y/n): " confirm
        [ "$confirm" != "y" ] && return
    fi
    
    if ! python3 -c "import sqlite3" 2>/dev/null; then
        echo "✗ 错误: sqlite3 不可用"
        return 1
    fi
    
    if [ ! -f "$DATA_FILE" ]; then
        echo "✗ 错误: table.json 不存在，无法加载翻译数据"
        read -p "继续? (y/n): " confirm
        [ "$confirm" != "y" ] && return
    fi
    
    if ! python3 -c "import check_translation" 2>/dev/null; then
        echo "✗ 错误: check_translation.py 加载失败"
        return 1
    fi
    
    enable_proxy
    exec python3 check_translation.py --port $PORT
}

show_status() {
    echo ""
    echo "状态检查:"
    echo "----------------------------------------"
    
    if python3 -c "import requests" 2>/dev/null; then
        echo "requests: ✓ 已安装"
    else
        echo "requests: ✗ 未安装"
    fi
    
    if python3 -c "import sqlite3" 2>/dev/null; then
        echo "sqlite3: ✓ 可用"
    else
        echo "sqlite3: ✗ 不可用"
    fi
    
    if [ -f "$DATA_FILE" ]; then
        echo "table.json: ✓ 存在"
    else
        echo "table.json: ✗ 不存在"
    fi
    
    if [ -f "$DB_FILE" ]; then
        TOTAL=$(python3 -c "import sqlite3; print(sqlite3.connect('$DB_FILE').cursor().execute('SELECT COUNT(*) FROM translation_status').fetchone()[0])" 2>/dev/null)
        FIXED=$(python3 -c "import sqlite3; print(sqlite3.connect('$DB_FILE').cursor().execute('SELECT COUNT(*) FROM translation_status WHERE is_fixed=1').fetchone()[0])" 2>/dev/null)
        echo "数据库: ✓ 已建立 ($TOTAL 条, $FIXED 条已修复)"
    else
        echo "数据库: ✗ 未建立"
    fi
    
    if check_proxy; then
        echo "代理: ✓ 已启用"
    else
        echo "代理: ✗ 未启用"
    fi
}

show_menu() {
    clear
    echo "========================================"
    echo "   翻译质量检查工具"
    echo "========================================"
    echo ""
    show_status
    echo ""
    echo "1. 启动服务"
    echo "2. 安装依赖"
    echo "3. 初始化数据库"
    echo "0. 退出"
    echo ""
    echo -n "请选择: "
}

while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_server ;;
        2) install_deps; echo ""; read -p "按回车继续..." ;;
        3) init_db; echo ""; read -p "按回车继续..." ;;
        0) exit 0 ;;
        *) echo "无效选择"; sleep 1 ;;
    esac
done
