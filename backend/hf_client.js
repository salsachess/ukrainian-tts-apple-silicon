const { client } = require("@gradio/client");

let ttsClient = null;
let stressClient = null;
let availableVoices = [];

// Ініціалізація (прогрів) — викликається по кнопці на Frontend
async function initHuggingFace() {
    try {
        console.log("Ініціалізація AI моделей...");
        
        if (process.env.HF_TOKEN) {
            console.log(`[Debug] Знайдено HF_TOKEN: ${process.env.HF_TOKEN.substring(0, 7)}...`);
        } else {
            console.log("[Debug] HF_TOKEN не знайдено, використовується анонімний доступ.");
        }

        // Створюємо спільні налаштування з токеном та заголовками для обох моделей
        const clientOptions = process.env.HF_TOKEN 
            ? { 
                token: process.env.HF_TOKEN,
                headers: { Authorization: `Bearer ${process.env.HF_TOKEN}` }
              } 
            : {};

        // Підключаємось до моделі наголосів (з обробкою помилки, якщо простір приватний або недоступний)
        try {
            stressClient = await client("patriotyk/ukrainian-accentor-transformer", clientOptions);
            console.log("Модель наголосів успішно підключена.");
            const stressApi = await stressClient.view_api();
            console.log("[Debug] Stress API:", JSON.stringify(stressApi, null, 2));
        } catch (e) {
            console.warn("Попередження: Не вдалося підключитися до моделі наголосів. Деталі:", e.message);
            stressClient = null;
        }

        // Підключаємось до основної TTS-моделі
        try {
            ttsClient = await client("patriotyk/styletts2-ukrainian", clientOptions);
            console.log("Основна TTS-модель успішно підключена.");
            const ttsApi = await ttsClient.view_api();
            console.log("[Debug] TTS API:", JSON.stringify(ttsApi, null, 2));
        } catch (e) {
            console.error("Помилка: Не вдалося підключитися до основної TTS-моделі. Деталі:", e.message);
            ttsClient = null;
        }

        // Встановлюємо реальні доступні голоси для моделі styletts2-ukrainian
        availableVoices = [
            'Інна Гелевера', 'Анастасія Павленко', 'Артем Окороков', 'Вʼячеслав Дудко', 
            'Вероніка Дорош', 'Влада Муравець', 'Вікторія Левченко', 'Гаська Шиян', 
            'Денис Денисенко', 'Катерина Потапенко', 'Кирило Татарченко', 'Людмила Чиркова', 
            'Марина Панас', 'Марися Нікітюк', 'Марта Мольфар', 'Марічка Штирбулова', 
            'Матвій Ніколаєв', 'Михайло Тишин', 'Олександр Ролдугін', 'Олена Шверк', 
            'Павло Буковський', 'Петро Філяк', 'Поліна Еккерт(хлопчик)', 'Поліна Еккерт', 
            'Роман Куліш', 'Слава Красовська', 'Тарас Василюк', 'Тетяна Гончарова', 
            'Тетяна Лукинюк', 'Юрій Вихованець', 'Юрій Кудрявець'
        ];

        console.log("AI успішно прогрітий. Доступні голоси:", availableVoices.length);
        return { status: "ready", voicesCount: availableVoices.length };
    } catch (error) {
        console.error("Помилка ініціалізації HF:", error);
        throw error;
    }
}

// Нормалізація тексту через модель наголосів
async function processText(text) {
    if (!stressClient) {
        console.log("Stress model not initialized, returning original text");

        return text; // Fallback: повертаємо текст як є
    }

    try {
        const result = await stressClient.predict("/predict", [text]);
        console.log("Origin text: ", text);
        console.log("Stressed text: ", result.data[0]);

        return result.data[0];
    } catch (e) {
        console.error("Помилка наголошення:", e);
        
        return text;
    }
}

// Вербалізація тексту (числа, дати, абревіатури → словесна форма)
async function verbalizeText(text) {
    if (!ttsClient) {
        console.log("TTS client not initialized, skipping verbalization");
        return text;
    }
    try {
        const result = await ttsClient.predict("/verbalize", [text]);
        console.log("Original text: ", text);
        console.log("Verbalized text: ", result.data[0]);
        return result.data[0];
    } catch (e) {
        console.error("Помилка вербалізації:", e);
        return text;
    }
}

// Генерація аудіо (повний пайплайн: verbalize → stress → synthesize)
async function generateAudio(text, voiceId) {
    if (!ttsClient) throw new Error("TTS модель не ініціалізована");

    // 1. Вербалізація (числа, дати → слова)
    const verbalizedText = await verbalizeText(text);

    // 2. Розстановка наголосів
    const stressedText = await processText(verbalizedText);

    // 3. Синтез аудіо
    const result = await ttsClient.predict("/synthesize", [
        "multi",        // model_name
        stressedText,   // text
        1,              // speed
        voiceId         // voice_name
    ]);

    // Gradio повертає об'єкт з URL на тимчасовий файл або буфер
    return result.data[0];
}

function getRandomVoice() {
    if (availableVoices.length === 0) return "default_voice";
    const randomIndex = Math.floor(Math.random() * availableVoices.length);
    return availableVoices[randomIndex];
}

function getStatus() {
    return {
        ttsClientInitialized: !!ttsClient,
        stressClientInitialized: !!stressClient,
        voicesCount: availableVoices.length,
        hasAccessToken: !!process.env.HF_TOKEN,
    };
}

module.exports = { initHuggingFace, generateAudio, getRandomVoice, getStatus };
