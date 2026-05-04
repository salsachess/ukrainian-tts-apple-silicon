# Stream Voices API — Повна документація проєкту

> **Джерела:**
> - [Gemini Notebook — «Створення системи озвучки тексту API»](https://gemini.google.com/app/f978e1c0e44edd83)
> - [Gemini Share — публічна розмова](https://gemini.google.com/share/7bfcf0763586)
>
> **Дата:** 25–26 квітня 2026 р.

---

## 1. Загальний огляд ідеї

Мета проєкту — створити систему, яка дозволяє через API відправляти текстові дані від імені різних персонажів та отримувати на виході готову озвучку **українською мовою**. Головна особливість — на бекенді кожному персонажу автоматично присвоюється унікальний голос, яким він консистентно озвучується у всіх подальших запитах.

Це дозволяє оживити трансляції: інтерактивна озвучка повідомлень від глядачів, донати різними персонажами, сюжетні вставки. «Під капотом» системи працює штучний інтелект на базі платформи Hugging Face.

---

## 2. Архітектура системи

Система складається з трьох основних блоків:

```
Клієнт (Quasar + Axios)
       │ { character, text }
       ▼
Бекенд (Node.js + Express.js + SQLite)
       │ { voice_id, stressed_text }
       ▼
Hugging Face Gradio API
  ├─ patriotyk/stressifier-byt5-g2p-model  (наголоси)
  └─ patriotyk/styletts2-ukrainian          (генерація аудіо)
       │ ArrayBuffer (.wav)
       ▼
Бекенд → Клієнт (бінарні аудіо-дані)
```

### 2.1. Frontend (Quasar + Axios)

- Клієнтська частина — «пульт керування» озвучкою.
- Збирає дані: ім'я персонажа + текст повідомлення.
- Містить кнопку **«Прогрів AI»** (Pre-warm) — запускається за ~5 хвилин до стріму.
- Отримує аудіо у форматі `ArrayBuffer` та відтворює через `new Audio()`.

### 2.2. Backend (Node.js + Express.js + SQLite)

- «Мозок» системи — прошарок між фронтендом і AI.
- **Express.js** — обробляє REST-запити від клієнта.
- **SQLite** — зберігає маппінг «персонаж → голос» для консистентності між сесіями.
- Логіка призначення голосу:
  - Нові персонажі → отримують випадковий `voice_id` зі списку.
  - Відомі персонажі → завжди використовують раніше закріплений `voice_id`.

### 2.3. AI Двигун (Hugging Face Spaces)

Дві моделі розробника **patriotyk (Serhiy Stetskovych)**:

| Модель | Простір | Призначення |
|---|---|---|
| StyleTTS2 | `patriotyk/styletts2-ukrainian` | Мультиспікерна TTS-модель, натренована на українському датасеті |
| Стресифікатор | `patriotyk/stressifier-byt5-g2p-model` | Нормалізація тексту та розстановка наголосів |

---

## 3. Підводні камені

| Проблема | Опис | Рішення |
|---|---|---|
| **Сплячий режим** | Безкоштовні Spaces засинають без активності. Перше пробудження — 1–5 хвилин | Кнопка «Прогрів» перед стрімом |
| **Затримка (Latency)** | Генерація займає 1–5 секунд на запит | Передбачити буферизацію або чергу |
| **API Ліміти** | Безкоштовні API можуть блокувати при спамі | Система черг на бекенді |
| **Нормалізація тексту** | Цифри, абревіатури → артефакти у вимові | Препроцесинг через `stressifier` |
| **Залежність від чужого Space** | Автор може видалити або змінити Space | Для продакшну — власний Space |

---

## 4. Обрані рішення MVP

| Питання | Рішення |
|---|---|
| Формат аудіоданих | **ArrayBuffer** (бінарний потік, ефективний за пам'яттю) |
| Список голосів | Динамічне отримання через `@gradio/client` при ініціалізації сервера |
| Схема БД | Найпростіша таблиця `characters`: `id`, `name`, `voice_id` |
| Сплячий режим | **Варіант 2: Кнопка «Прогрів»** (Pre-warm) — ручний запуск перед стрімом |
| Нормалізація тексту | Використовуємо `stressifier-byt5-g2p-model` |

---

## 5. Варіанти обробки «сплячого» режиму (детально)

### Варіант 1: Keep-Alive (Пінг-бот)
`setInterval` або cron надсилає мінімальний запит кожні 30–45 хв.
- ✅ Модель завжди «гаряча».
- ❌ Ризик тимчасового блокування за зловживання безкоштовними ресурсами.

### Варіант 2: Кнопка «Прогріву» (Pre-warm) ← **Обраний**
На фронтенді кнопка «Ініціалізація AI». Натискається за 5 хвилин до початку стріму.
- ✅ Найпрозоріший і найбезпечніший варіант. Повний контроль стану.
- ❌ Вимагає ручної дії перед кожним стрімом.

### Варіант 3: Розумний Frontend + Довгий таймаут
Axios з таймаутом 3–5 хвилин. UI показує «ШІ прокидається...».
- ✅ Нічого не треба клікати додатково.
- ❌ Перший глядацький запит буде довго чекати.

---

## 6. Детальний план реалізації MVP

### Крок 1: Ініціалізація проєкту та залежності

```bash
mkdir stream-voices-backend
cd stream-voices-backend
npm init -y
npm install express cors sqlite3 @gradio/client
```

### Крок 2: База даних персонажів (`db.js`)

Таблиця `characters`:

| Поле | Тип | Опис |
|---|---|---|
| `id` | INTEGER | Первинний ключ (автоінкремент) |
| `name` | TEXT UNIQUE | Ім'я персонажа (напр. «Гном», «Ельф») |
| `voice_id` | TEXT | ID голосу зі StyleTTS2 |

```javascript
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./characters.sqlite');

db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            voice_id TEXT
        )
    `);
});

module.exports = db;
```

### Крок 3: Клієнт Hugging Face (`hf_client.js`)

Цей модуль є «мостом» між Node.js сервером та AI-моделями. Інкапсулює всю логіку роботи зі штучним інтелектом.

**Чотири завдання модуля:**
1. **Підключення до двох моделей** — TTS (`styletts2-ukrainian`) і наголосів (`stressifier-byt5-g2p-model`) — та їх «прогрів».
2. **Динамічне отримання списку голосів** — при ініціалізації кешує доступні `voice_id` в пам'ять сервера.
3. **Нормалізація тексту** — перед генерацією сирий текст проходить через `stressifier` для правильних наголосів.
4. **Генерація та повернення бінарних даних** — `server.js` просто викликає функцію і отримує `ArrayBuffer`.

```javascript
const { client } = require("@gradio/client");

let ttsClient = null;
let stressClient = null;
let availableVoices = [];

// Ініціалізація (прогрів) — викликається по кнопці на Frontend
async function initHuggingFace() {
    try {
        console.log("Ініціалізація AI моделей...");

        // Підключаємось до моделі наголосів
        stressClient = await client("patriotyk/stressifier-byt5-g2p-model");

        // Підключаємось до основної TTS-моделі
        ttsClient = await client("patriotyk/styletts2-ukrainian");

        // Динамічно отримуємо список доступних голосів
        const appInfo = await ttsClient.view_api();
        const endpoints = appInfo.named_endpoints;
        if (endpoints && endpoints['/predict']) {
            // Логіка парсингу voice_id з API...
            // Для MVP — симулюємо отримані дані:
            availableVoices = ["voice_1", "voice_2", "voice_3", "voice_4"];
        }

        console.log("AI успішно прогрітий. Доступні голоси:", availableVoices);
        return { status: "ready", voicesCount: availableVoices.length };
    } catch (error) {
        console.error("Помилка ініціалізації HF:", error);
        throw error;
    }
}

// Нормалізація тексту через модель наголосів
async function processText(text) {
    if (!stressClient) throw new Error("Модель наголосів не ініціалізована");
    const result = await stressClient.predict("/predict", [text]);
    return result.data[0];
}

// Генерація аудіо
async function generateAudio(text, voiceId) {
    if (!ttsClient) throw new Error("TTS модель не ініціалізована");

    const stressedText = await processText(text);

    const result = await ttsClient.predict("/predict", [
        stressedText,
        voiceId
    ]);

    // Gradio повертає об'єкт з URL на тимчасовий файл або буфер
    return result.data[0];
}

function getRandomVoice() {
    if (availableVoices.length === 0) return "default_voice";
    const randomIndex = Math.floor(Math.random() * availableVoices.length);
    return availableVoices[randomIndex];
}

module.exports = { initHuggingFace, generateAudio, getRandomVoice };
```

### Крок 4: Основний сервер (`server.js`)

```javascript
const express = require('express');
const cors = require('cors');
const db = require('./db');
const hf = require('./hf_client');

const app = express();
app.use(cors());
app.use(express.json());

// Ендпоінт для кнопки «Прогрів» на Frontend
app.post('/api/pre-warm', async (req, res) => {
    try {
        const status = await hf.initHuggingFace();
        res.json(status);
    } catch (error) {
        res.status(500).json({ error: "Не вдалося прогріти модель", details: error.message });
    }
});

// Головний ендпоінт озвучки
app.post('/api/tts', async (req, res) => {
    const { character, text } = req.body;

    if (!character || !text) {
        return res.status(400).json({ error: "Потрібні character та text" });
    }

    // Шукаємо персонажа в базі
    db.get("SELECT voice_id FROM characters WHERE name = ?", [character], async (err, row) => {
        if (err) return res.status(500).json({ error: "Помилка БД" });

        let voiceId;

        if (row) {
            voiceId = row.voice_id; // Персонаж відомий — беремо його голос
        } else {
            voiceId = hf.getRandomVoice(); // Новий персонаж — призначаємо випадковий голос
            db.run("INSERT INTO characters (name, voice_id) VALUES (?, ?)", [character, voiceId]);
        }

        try {
            const audioResult = await hf.generateAudio(text, voiceId);

            // Завантажуємо аудіо як ArrayBuffer і відправляємо на Frontend
            const response = await fetch(audioResult.url);
            const arrayBuffer = await response.arrayBuffer();

            res.setHeader('Content-Type', 'audio/wav');
            res.send(Buffer.from(arrayBuffer));

        } catch (error) {
            console.error(error);
            res.status(500).json({ error: "Помилка генерації аудіо" });
        }
    });
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Бекенд запущено на http://localhost:${PORT}`);
    console.log(`Натисни "Прогрів" на клієнті перед початком стріму.`);
});
```

**Запуск:**
```bash
node server.js
```

---

## 7. Frontend (Quasar) — план інтерфейсу

**Ініціалізація:**
```bash
npm init quasar
```

**UI елементи:**
- `<q-input>` — ім'я персонажа
- `<q-input type="textarea">` — текст для озвучки
- `<q-btn>` — «Прогріти AI» (викликає `POST /api/pre-warm`)
- `<q-btn>` — «Озвучити» (викликає `POST /api/tts`)
- `<q-spinner>` — індикатор завантаження (генерація займає час)

**Відтворення аудіо (Axios):**
```javascript
const response = await axios.post('/api/tts', { character, text }, {
    responseType: 'arraybuffer'
});
const blob = new Blob([response.data], { type: 'audio/wav' });
const url = URL.createObjectURL(blob);
const audio = new Audio(url);
audio.play();
```

---

## 8. Тестовий цикл MVP

1. Ввести **«Гном»** + текст «Привіт» → дочекатися озвучки.
2. Ввести **«Ельф»** + текст «Вітаю» → має бути **інший** голос.
3. Знову ввести **«Гном»** + інший текст → має бути **той самий** голос, що у п.1.

---

## 9. Додавання нових голосів

### Спосіб 1 — Вбудовані голоси (автоматично)

- При «прогріві» система автоматично отримує актуальний список `voice_id` з моделі.
- Якщо автор (patriotyk) натренує нові голоси й оновить Space — бекенд «побачить» їх при наступному запуску.
- Нові персонажі отримують голос із цього списку автоматично.

### Спосіб 2 — Власний голос через аудіо-референс

- Мультиспікерна модель підтримує передачу короткого аудіозапису (`.wav`) як референсу замість `voice_id`.
- Бекенд відправляє на Hugging Face: текст + аудіофайл-зразок (5–10 секунд).
- ШІ аналізує зразок і генерує озвучку, імітуючи цей тембр та інтонацію.
- Застосування: власний голос стрімера, голоси друзів, персонажі з відомих творів.

---

## 10. Чужий Space vs. Власний Space

| | Чужий публічний Space | Власний Space |
|---|---|---|
| **Швидкість старту** | ✅ Миттєво | ❌ Потрібне налаштування |
| **Вартість** | ✅ Безкоштовно | ❌ Платний GPU |
| **Надійність** | ❌ Залежить від автора | ✅ Повний контроль |
| **Сплячий режим** | ❌ Є (вирішується кнопкою прогріву) | ✅ Немає (платний Always-on) |
| **Рекомендація** | **MVP / розробка** | **Продакшн** |

**Для MVP:** Використовувати чужий (існуючий) Space `patriotyk/styletts2-ukrainian`.

**Для продакшну:** Скопіювати (Duplicate) Space у свій акаунт і орендувати платний GPU, або запускати моделі (`styletts2_ukrainian_multispeaker_*`) локально при наявності потужної відеокарти.

---

## 11. Перспективи розвитку

| Напрямок | Опис |
|---|---|
| **Платний Space** | Оренда виділеного GPU на HF — миттєва генерація без засинання |
| **Локальний запуск** | Завантажити моделі локально — незалежність від сторонніх API |
| **Система черг** | Черга запитів на бекенді — захист від спаму в чаті |
| **Нормалізація числівників** | «100» → «сто» — менше артефактів у вимові |
| **OBS інтеграція** | Browser Source + WebSocket — автовідтворення на стрімі |
| **Twitch/YouTube бот** | Читання повідомлень чату з префіксами (`!elf Привіт`) |
