# Локальний запуск на Mac (Apple Silicon + MPS)

> Ця інструкція описує як розгорнути StyleTTS2 та Ukrainian Accentor на Mac з Apple Silicon (M1/M2/M3).
> Після цього бекенд зможе працювати без залежності від Hugging Face Spaces.

---

## Вимоги

| Компонент | Мінімум | Рекомендовано |
|---|---|---|
| **Mac** | Apple Silicon (M1) | M1 Pro / M2 Pro+ |
| **macOS** | 12.3 (Monterey) | Tahoe (16) |
| **RAM** | 16 GB | 16 GB+ |
| **Диск** | ~5 GB (моделі + venv) | SSD |
| **Homebrew** | Встановлений | — |
| **Python** | 3.10+ | 3.12 |
| **Node.js** | 18+ | 22+ |

---

## Швидкий старт

### 1. Клонуйте репозиторій

```bash
git clone <repo-url> voices-on-the-stream
cd voices-on-the-stream
```

### 2. Запустіть налаштування (одноразово)

```bash
chmod +x scripts/setup_mac.sh
./scripts/setup_mac.sh
```

Скрипт автоматично:
- Перевірить Homebrew, Python, espeak-ng, Node.js
- Створить Python venv з PyTorch MPS
- Встановить всі залежності
- Створить `backend/.env`

### 3. Запустіть всі сервіси

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

Запускає:
- 🔤 **Accentor** — http://localhost:7861 (наголоси, CPU)
- 🔊 **TTS** — http://localhost:7860 (синтез, MPS GPU)
- 🖥️ **Backend** — http://localhost:3000 (API)

### 4. Запустіть фронтенд (в окремому терміналі)

```bash
cd frontend
npm run dev
```

### 5. Відкрийте http://localhost:5173 і натисніть «Прогрів»

---

## Ручний запуск (кожен сервіс окремо)

Якщо потрібен більший контроль:

```bash
# Термінал 1: Accentor
source scripts/.venv/bin/activate
python scripts/run_accentor.py

# Термінал 2: TTS
source scripts/.venv/bin/activate
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/run_tts.py

# Термінал 3: Backend
cd backend
node server.js

# Термінал 4: Frontend
cd frontend
npm run dev
```

---

## Перевірка

### MPS доступність
```bash
source scripts/.venv/bin/activate
python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```

### Прогрів бекенду
```bash
curl -X POST http://localhost:3000/api/pre-warm
```

Відповідь:
```json
{"status": "ready", "mode": "local", "voicesCount": 31}
```

### Тест генерації
```bash
curl -X POST http://localhost:3000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"character": "Тест", "text": "Привіт, це тестове повідомлення."}' \
  --output test.wav
```

### Статус системи
```bash
curl http://localhost:3000/api/status
```

---

## Порівняння режимів

| | `TTS_MODE=huggingface` | `TTS_MODE=local` |
|---|---|---|
| **Де працює модель** | Сервери HF (ZeroGPU) | M1 Pro (MPS) |
| **Затримка** | 2–10 сек (мережа + GPU) | ~1–3 сек |
| **Сплячий режим** | Є (прогрів 1–5 хв) | Немає |
| **Ліміти квоти** | Є (ZeroGPU quota exceeded) | Немає |
| **Вимоги** | HF_TOKEN + Інтернет | Python + MPS |
| **Надійність** | Залежить від HF | Повний контроль |

---

## Перемикання між режимами

```bash
# Локальний (Mac MPS)
# в backend/.env:
TTS_MODE=local

# Хмарний (HF Spaces)
# в backend/.env:
TTS_MODE=huggingface
```

Після зміни перезапустіть бекенд: `node server.js`

---

## Структура файлів

```
voices-on-the-stream/
├── scripts/
│   ├── setup_mac.sh          ← Одноразове налаштування
│   ├── start.sh              ← Запуск всіх сервісів
│   ├── run_tts.py            ← Gradio TTS-сервер (MPS)
│   ├── run_accentor.py       ← Gradio Accentor-сервер (CPU)
│   ├── requirements-mac.txt  ← Python залежності
│   └── .venv/                ← Python venv (створюється setup_mac.sh)
├── backend/
│   ├── server.js             ← Node.js API
│   ├── ai_client.js          ← Gradio клієнт
│   ├── db.js                 ← SQLite
│   └── .env                  ← Конфігурація
├── frontend/
│   └── ...                   ← Quasar/Vue UI
└── docs/
    └── mac-setup.md          ← Ця інструкція
```

---

## Troubleshooting

### MPS не доступний
```
MPS: False
```
→ Переконайтесь, що macOS ≥ 12.3 і PyTorch ≥ 2.0. Оновіть:
```bash
pip install --upgrade torch torchaudio
```

### Помилка "MPS does not support operation X"
→ Запускайте з fallback:
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/run_tts.py
```
Unsupported операції автоматично виконуватимуться на CPU.

### Перший запуск дуже повільний
При першому старті завантажуються моделі з HuggingFace Hub (~2–5 GB). 
Далі вони кешуються в `~/.cache/huggingface`.

### espeak-ng не знайдено
```bash
brew install espeak-ng
```

### Помилка phonemizer
```bash
pip install phonemizer
```
Переконайтесь, що espeak-ng встановлено і доступний у PATH.

### NLTK punkt не знайдено
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```
