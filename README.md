# 🇺🇦 Ukrainian TTS for Apple Silicon

Цей проект є адаптацією та розширенням роботи [Patriotyk](https://github.com/patriotyk/styletts2-ukrainian) для локального запуску на **macOS (Apple Silicon)**. Він дозволяє синтезувати високоякісний український голос без необхідності мати відеокарту NVIDIA (CUDA).

## ✨ Особливості
- **Оптимізовано для Mac:** Використовує PyTorch MPS (Metal Performance Shaders) для прискорення на чипах M1, M2, M3.
- **Локальний запуск:** Жодних хмарних запитів, повна приватність та робота офлайн.
- **Багатоголосий синтез:** Підтримка десятків голосів, включаючи клоновані.
- **Повний стек:** Включає Backend (Node.js) та Frontend (Vue.js) для зручного користування.

## 🚀 Швидкий старт (Mac)

1. **Клонуйте репозиторій:**
   ```bash
   git clone https://github.com/salsachess/ukrainian-tts-apple-silicon.git
   cd ukrainian-tts-apple-silicon
   ```

2. **Запустіть автоматичне налаштування:**
   ```bash
   chmod +x scripts/setup_mac.sh
   ./scripts/setup_mac.sh
   ```
   *Скрипт встановить усі залежності (Python venv, Node.js, PyTorch MPS).*

3. **Запустіть проект:**
   ```bash
   ./scripts/start.sh
   ```

## 🛠 Технології
- **TTS Engine:** [StyleTTS2](https://github.com/gjndai/StyleTTS2)
- **Моделі:** [patriotyk/styletts2-ukrainian](https://huggingface.co/patriotyk/styletts2-ukrainian)
- **Прискорення:** Apple Metal (MPS)
- **Інтерфейс:** Vue.js + Node.js

## 🙏 Подяка
Велика подяка [Patriotyk](https://github.com/patriotyk) за тренування моделей та розвиток українського синтезу мовлення.

---
*Проект створено для популяризації українського ШІ та спрощення доступу до сучасних технологій на платформі Mac.*
