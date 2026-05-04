#!/bin/bash
# ============================================================
# setup_mac.sh — Налаштування середовища для Apple Silicon Mac
# ============================================================
# Запуск: chmod +x scripts/setup_mac.sh && ./scripts/setup_mac.sh
# Потрібно: Homebrew, Python 3.10+

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "================================================"
echo "  Voices on the Stream — Mac Setup"
echo "  Apple Silicon (M1/M2/M3) + PyTorch MPS"
echo "================================================"
echo ""

# --- 1. Перевірка Homebrew ---
echo "🔍 Перевірка Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew не знайдено. Встановіть з https://brew.sh"
    echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi
echo "✅ Homebrew: $(brew --version | head -1)"

# --- 2. Перевірка Python ---
echo ""
echo "🔍 Перевірка Python..."
PYTHON_CMD=""
for cmd in python3.10 python3.11 python3.12 python3.13 python3; do
    if command -v "$cmd" &> /dev/null; then
        PY_VERSION=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.10+ не знайдено. Встановіть:"
    echo "   brew install python@3.10"
    exit 1
fi
echo "✅ Python: $($PYTHON_CMD --version)"

# --- 3. Встановлення espeak-ng ---
echo ""
echo "🔍 Перевірка espeak-ng..."
if ! command -v espeak-ng &> /dev/null; then
    echo "📦 Встановлення espeak-ng..."
    brew install espeak-ng
else
    echo "✅ espeak-ng: $(espeak-ng --version 2>&1 | head -1)"
fi

# --- 4. Встановлення Node.js (для backend) ---
echo ""
echo "🔍 Перевірка Node.js..."
if ! command -v node &> /dev/null; then
    echo "📦 Встановлення Node.js..."
    brew install node
else
    echo "✅ Node.js: $(node --version)"
fi

# --- 5. Створення Python venv ---
echo ""
echo "🐍 Створення Python venv у $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  venv вже існує. Перестворити? (y/N)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# Активація
source "$VENV_DIR/bin/activate"
echo "✅ venv активовано: $(python --version)"

# --- 6. Встановлення pip залежностей ---
echo ""
echo "📦 Встановлення Python залежностей (це може зайняти 5-10 хвилин)..."
pip install --upgrade pip

# Спочатку PyTorch (без CUDA)
echo ""
echo "🔥 Встановлення PyTorch з підтримкою MPS..."
pip install torch torchaudio

# Решта залежностей
echo ""
echo "📦 Встановлення StyleTTS2 та інших залежностей..."
pip install -r "$SCRIPT_DIR/requirements-mac.txt"

# NLTK дані (потрібні для word_tokenize)
echo ""
echo "📦 Завантаження NLTK даних..."
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# --- 7. Перевірка MPS ---
echo ""
echo "🔍 Перевірка PyTorch MPS..."
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'MPS available: {torch.backends.mps.is_available()}')
print(f'MPS built: {torch.backends.mps.is_built()}')
if torch.backends.mps.is_available():
    x = torch.ones(3, device='mps')
    print(f'MPS tensor test: {x} ✅')
else:
    print('⚠️  MPS недоступний, буде використовуватися CPU')
"

# --- 8. Встановлення npm залежностей бекенду ---
echo ""
echo "📦 Встановлення npm залежностей бекенду..."
cd "$SCRIPT_DIR/../backend"
npm install
cd "$SCRIPT_DIR"

# --- 9. Встановлення npm залежностей фронтенду ---
echo ""
echo "📦 Встановлення npm залежностей фронтенду..."
cd "$SCRIPT_DIR/../frontend"
npm install
cd "$SCRIPT_DIR"

# --- 10. Налаштування .env ---
echo ""
ENV_FILE="$SCRIPT_DIR/../backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Створення backend/.env..."
    cat > "$ENV_FILE" << 'EOF'
# Режим генерації: "huggingface" (HF Spaces) або "local" (нативний Python + MPS)
TTS_MODE=local

# === Hugging Face Settings (TTS_MODE=huggingface) ===
HF_TOKEN=your_hugging_face_access_token_here

# === Local Settings (TTS_MODE=local) ===
LOCAL_TTS_URL=http://localhost:7860
LOCAL_STRESS_URL=http://localhost:7861
EOF
    echo "✅ .env створено з TTS_MODE=local"
else
    echo "✅ .env вже існує (перевір TTS_MODE=local)"
fi

# --- Готово ---
echo ""
echo "================================================"
echo "  ✅ Налаштування завершено!"
echo "================================================"
echo ""
echo "Для запуску всього стеку:"
echo "  ./scripts/start.sh"
echo ""
echo "Або вручну (кожен у окремому терміналі):"
echo "  1. source scripts/.venv/bin/activate && python scripts/run_accentor.py"
echo "  2. source scripts/.venv/bin/activate && PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/run_tts.py"
echo "  3. cd backend && node server.js"
echo "  4. cd frontend && npm run dev"
echo ""
echo "⚠️  Перший запуск TTS завантажить моделі (~2-5 GB) з HuggingFace Hub."
echo ""
