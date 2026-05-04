#!/bin/bash
# ============================================================
# start.sh — Запуск всього стеку Voices on the Stream
# ============================================================
# Запускає: Accentor (7861) → TTS (7860) → Backend (3000)
# Натисніть Ctrl+C для зупинки всіх процесів.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/.venv"

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  🎙️  Voices on the Stream — Start${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# --- Перевірка venv ---
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Python venv не знайдено. Спочатку запустіть:${NC}"
    echo "   ./scripts/setup_mac.sh"
    exit 1
fi

# Активація venv
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✅ Python venv активовано${NC}"

# MPS fallback для unsupported ops
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Завантаження .env з бекенду (для HF_TOKEN)
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    echo -e "${GREEN}✅ Завантаження змінних середовища з backend/.env${NC}"
    set -a
    source "$PROJECT_DIR/backend/.env"
    set +a
fi

# --- PID tracking для graceful shutdown ---
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Зупинка всіх процесів...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo -e "  Зупинено PID $pid"
        fi
    done
    wait 2>/dev/null
    echo -e "${GREEN}✅ Всі процеси зупинено.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# --- 1. Запуск Accentor ---
echo ""
echo -e "${YELLOW}🔤 Запуск Accentor (порт 7861)...${NC}"
python "$SCRIPT_DIR/run_accentor.py" &
PIDS+=($!)
echo -e "  PID: $!"

# Чекаємо поки Accentor стартує
sleep 3

# --- 2. Запуск TTS ---
echo ""
echo -e "${YELLOW}🔊 Запуск TTS (порт 7860, device=MPS)...${NC}"
python "$SCRIPT_DIR/run_tts.py" &
PIDS+=($!)
echo -e "  PID: $!"

# Чекаємо поки TTS стартує (завантаження моделей може зайняти час)
echo -e "${YELLOW}  ⏳ Очікування готовності TTS моделі на порту 7860...${NC}"
while ! curl -s http://localhost:7860 > /dev/null; do
    sleep 2
done
echo -e "${GREEN}  🟢 TTS модель готова!${NC}"

# --- 3. Запуск Backend ---
echo ""
echo -e "${YELLOW}🖥️  Запуск Node.js Backend (порт 3000)...${NC}"
cd "$PROJECT_DIR/backend"
node server.js &
PIDS+=($!)
echo -e "  PID: $!"
cd "$SCRIPT_DIR"

# --- Авто-прогрів (Pre-warm) ---
echo ""
echo -e "${YELLOW}⏳ Автоматична ініціалізація AI моделей...${NC}"
# Чекаємо 2 секунди, щоб Node.js встиг підняти порт
sleep 2 
curl -s -X POST http://localhost:3000/api/pre-warm > /dev/null
echo -e "${GREEN}✨ AI системи готові до роботи!${NC}"

# --- Готово ---
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ Всі сервіси запущено!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  🔤 Accentor:  http://localhost:7861"
echo -e "  🔊 TTS:       http://localhost:7860"
echo -e "  🖥️  Backend:   http://localhost:3000"
echo ""
echo -e "  Відкрийте фронтенд у іншому терміналі:"
echo -e "  ${BLUE}cd frontend && npm run dev${NC}"
echo ""
echo -e "  Натисніть ${RED}Ctrl+C${NC} для зупинки всіх процесів."
echo ""

# Чекаємо на завершення (Ctrl+C)
wait
