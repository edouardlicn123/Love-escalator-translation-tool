#!/bin/bash
# Translation Quality Check Tool - Startup Script

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
    echo "Installing dependencies..."

    if ! python3 -c "import requests" 2>/dev/null; then
        python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null
        pip3 install requests pysocks --break-system-packages 2>/dev/null
        echo "✓ requests, pysocks installed"
    else
        echo "✓ Dependencies installed"
    fi
}

init_db() {
    echo "Initializing database..."

    if [ ! -f "$DATA_FILE" ]; then
        echo "✗ Error: table.json not found"
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
print(f'✓ Inserted: {result[\"inserted\"]} entries')
print(f'✓ Updated: {result[\"updated\"]} entries')
"
}

start_server() {
    echo "Starting server..."

    if ! python3 -c "import requests" 2>/dev/null; then
        echo "⚠ Warning: requests not installed, run option 2 first"
        read -p "Continue? (y/n): " confirm
        [ "$confirm" != "y" ] && return
    fi

    if ! python3 -c "import sqlite3" 2>/dev/null; then
        echo "✗ Error: sqlite3 not available"
        return 1
    fi

    if [ ! -f "$DATA_FILE" ]; then
        echo "✗ Error: table.json not found, cannot load translation data"
        read -p "Continue? (y/n): " confirm
        [ "$confirm" != "y" ] && return
    fi

    if ! python3 -c "import check_translation" 2>/dev/null; then
        echo "✗ Error: check_translation.py failed to load"
        return 1
    fi

    enable_proxy
    exec python3 check_translation.py --port $PORT
}

copy_table() {
    echo "Copying table.json..."

    TARGET_DIR="/home/edo/loveEscalatorTL"
    TARGET_FILE="$TARGET_DIR/table.json"

    if [ ! -f "$DATA_FILE" ]; then
        echo "✗ Error: table.json not found"
        return 1
    fi

    if [ -f "$TARGET_FILE" ]; then
        echo "⚠ Target file already exists: $TARGET_FILE"
        echo -n "Overwrite? (y/n): "
        read confirm
        if [ "$confirm" != "y" ]; then
            echo "Cancelled"
            return 0
        fi
    fi

    if [ ! -d "$TARGET_DIR" ]; then
        mkdir -p "$TARGET_DIR"
    fi

    cp "$DATA_FILE" "$TARGET_FILE"

    if [ $? -eq 0 ]; then
        echo "✓ Copied to $TARGET_FILE"
    else
        echo "✗ Copy failed"
    fi
}

kill_server() {
    echo "Killing process..."
    pkill -f "check_translation.py" 2>/dev/null
    sleep 1
    echo "✓ Process terminated"
}

show_status() {
    echo ""
    echo "Status Check:"
    echo "----------------------------------------"

    if python3 -c "import requests" 2>/dev/null; then
        echo "requests: ✓ installed"
    else
        echo "requests: ✗ not installed"
    fi

    if python3 -c "import sqlite3" 2>/dev/null; then
        echo "sqlite3: ✓ available"
    else
        echo "sqlite3: ✗ not available"
    fi

    if [ -f "$DATA_FILE" ]; then
        echo "table.json: ✓ exists"
    else
        echo "table.json: ✗ not found"
    fi

    if [ -f "$DB_FILE" ]; then
        TOTAL=$(python3 -c "import sqlite3; print(sqlite3.connect('$DB_FILE').cursor().execute('SELECT COUNT(*) FROM translation_status').fetchone()[0])" 2>/dev/null)
        FIXED=$(python3 -c "import sqlite3; print(sqlite3.connect('$DB_FILE').cursor().execute('SELECT COUNT(*) FROM translation_status WHERE is_fixed=1').fetchone()[0])" 2>/dev/null)
        echo "Database: ✓ established ($TOTAL entries, $FIXED fixed)"
    else
        echo "Database: ✗ not established"
    fi

    if check_proxy; then
        echo "Proxy: ✓ enabled"
    else
        echo "Proxy: ✗ not enabled"
    fi
}

show_menu() {
    clear
    echo "========================================"
    echo "   Translation Quality Check Tool"
    echo "========================================"
    echo ""
    show_status
    echo ""
    echo "1. Start Server"
    echo "2. Install Dependencies"
    echo "3. Initialize Database"
    echo "4. Transfer Translation File"
    echo "9. Kill Process"
    echo "0. Exit"
    echo ""
    echo -n "Please select: "
}

while true; do
    show_menu
    read choice

    case $choice in
        1) start_server ;;
        2) install_deps; echo ""; read -p "Press Enter to continue..." ;;
        3) init_db; echo ""; read -p "Press Enter to continue..." ;;
        4) copy_table; echo ""; read -p "Press Enter to continue..." ;;
        9) kill_server; echo ""; read -p "Press Enter to continue..." ;;
        0) exit 0 ;;
        *) echo "Invalid selection"; sleep 1 ;;
    esac
done