#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# JulyFlow — Desktop Application Launcher
# Khởi chạy ứng dụng học từ vựng tiếng Anh giao diện Tokyo Night
# ═══════════════════════════════════════════════════════════════

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8765
URL="http://127.0.0.1:${PORT}"

echo "🌊 Starting JulyFlow Desktop Application..."

# 1. Kiểm tra xem server đã chạy chưa
if ! lsof -i:${PORT} >/dev/null 2>&1 && ! ss -lptn 'sport = :8765' | grep -q 8765; then
    echo "⚡ Launching JulyFlow Python Backend Server..."
    python3 "${APP_DIR}/server.py" ${PORT} > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 0.8
else
    echo "ℹ️ Backend server is already running on port ${PORT}."
fi

# 2. Khởi chạy cửa sổ ứng dụng Desktop độc lập (Standalone App Mode)
if command -v chromium >/dev/null 2>&1; then
    echo "🖥️ Launching Standalone Desktop Window (Chromium App Mode)..."
    chromium --app="${URL}" --class=JulyFlow --name="JulyFlow" >/dev/null 2>&1 &
elif command -v brave >/dev/null 2>&1; then
    echo "🖥️ Launching Standalone Desktop Window (Brave App Mode)..."
    brave --app="${URL}" --class=JulyFlow --name="JulyFlow" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
    echo "🌐 Opening JulyFlow in your default browser..."
    xdg-open "${URL}" >/dev/null 2>&1 &
elif command -v firefox >/dev/null 2>&1; then
    firefox "${URL}" >/dev/null 2>&1 &
fi

echo "✅ JulyFlow is now running at ${URL}"

