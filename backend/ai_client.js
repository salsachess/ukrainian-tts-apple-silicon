const { client } = require("@gradio/client");

let ttsClient = null;
let stressClient = null;
let stressEndpoint = "/predict"; // визначається автоматично при ініціалізації
let availableVoices = [];
let currentMode = null;

/**
 * Визначає режим роботи з .env
 * @returns {"huggingface" | "local"}
 */
function getMode() {
    const mode = (process.env.TTS_MODE || "huggingface").toLowerCase();
    if (mode !== "huggingface" && mode !== "local") {
        console.warn(`[AI] Невідомий TTS_MODE="${mode}", використовується "huggingface"`);
        return "huggingface";
    }
    return mode;
}

// Ініціалізація (прогрів) — викликається по кнопці на Frontend
async function initAI() {
    try {
        currentMode = getMode();
        console.log(`Ініціалізація AI моделей (режим: ${currentMode})...`);

        let ttsTarget, stressTarget, clientOptions;

        if (currentMode === "local") {
            // Локальний режим: підключаємось до Gradio-серверів на localhost
            ttsTarget = process.env.LOCAL_TTS_URL || "http://localhost:7860";
            stressTarget = process.env.LOCAL_STRESS_URL || "http://localhost:7861";
            clientOptions = {};
            console.log(`[Local] TTS URL: ${ttsTarget}`);
            console.log(`[Local] Stress URL: ${stressTarget}`);
        } else {
            // Hugging Face режим: підключаємось до віддалених Spaces
            ttsTarget = "patriotyk/styletts2-ukrainian";
            stressTarget = "patriotyk/ukrainian-accentor-transformer";
            clientOptions = process.env.HF_TOKEN 
                ? { 
                    token: process.env.HF_TOKEN,
                    headers: { Authorization: `Bearer ${process.env.HF_TOKEN}` }
                  } 
                : {};

            if (process.env.HF_TOKEN) {
                console.log(`[HF] Знайдено HF_TOKEN: ${process.env.HF_TOKEN.substring(0, 7)}...`);
            } else {
                console.log("[HF] HF_TOKEN не знайдено, використовується анонімний доступ.");
            }
        }

        // Підключаємось до моделі наголосів
        try {
            stressClient = await client(stressTarget, clientOptions);
            console.log("Модель наголосів успішно підключена.");
            const stressApi = await stressClient.view_api();
            console.log("[Debug] Stress API:", JSON.stringify(stressApi, null, 2));

            // Автовизначення ендпоінта: /predict (HF) або /accentification (local)
            const endpoints = Object.keys(stressApi.named_endpoints || {});
            if (endpoints.length > 0) {
                stressEndpoint = endpoints[0];
                console.log(`[Stress] Використовується ендпоінт: ${stressEndpoint}`);
            }
        } catch (e) {
            console.warn("Попередження: Не вдалося підключитися до моделі наголосів. Деталі:", e.message);
            stressClient = null;
        }

        // Підключаємось до основної TTS-моделі
        try {
            ttsClient = await client(ttsTarget, clientOptions);
            console.log("Основна TTS-модель успішно підключена.");
            const ttsApi = await ttsClient.view_api();
            console.log("[Debug] TTS API:", JSON.stringify(ttsApi, null, 2));
        } catch (e) {
            console.error("Помилка: Не вдалося підключитися до основної TTS-моделі. Деталі:", e.message);
            ttsClient = null;
        }

        // Отримуємо реальні доступні голоси з API моделі динамічно
        try {
            const ttsApi = await ttsClient.view_api();
            // Шукаємо випадаючий список голосів у метаданих API
            const voiceParam = ttsApi.named_endpoints["/synthesize"]?.parameters.find(p => p.label === "Voice");
            if (voiceParam && voiceParam.python_type && voiceParam.python_type.type.includes("Literal")) {
                // Витягуємо список з Literal['Голос1', 'Голос2', ...]
                const match = voiceParam.python_type.type.match(/Literal\[(.*)\]/);
                if (match) {
                    availableVoices = match[1].split(", ").map(v => v.replace(/'/g, ""));
                }
            }
        } catch (e) {
            console.warn("[AI] Не вдалося отримати список голосів динамічно, використовується резервний список.");
        }

        // Резервний список (якщо динамічне отримання не спрацювало)
        if (availableVoices.length === 0) {
            availableVoices = [
                'Інна Гелевера', 'Анастасія Павленко', 'Артем Окороков', 'Вʼячеслав Дудко', 
                'Вероніка Дорош', 'Влада Муравець', 'Вікторія Левченко', 'Гаська Шиян', 
                'Денис Денисенко', 'Катерина Потапенко', 'Кирило Татарченко', 'Людмила Чиркова', 
                'Марина Панас', 'Марися Нікітюк', 'Марта Мольфар', 'Марічка Штирбулова', 
                'Матвій Ніколаєв', 'Михайло Тишин', 'Олександр Ролдугін', 'Олена Шверк', 
                'Павло Буковський', 'Петро Філяк', 'Поліна Еккерт(хлопчик)', 'Поліна Еккерт', 
                'Роман Куліш', 'Слава Красовська', 'Тарас Василюк', 'Тетяна Гончарова', 
                'Тетяна Лукинюк', 'Юрій Вихованець', 'Юрій Кудрявець', 'Сергій_Франчук', 'сальсачес-піднесений'
            ];
        }

        console.log(`AI успішно прогрітий (${currentMode}). Доступні голоси:`, availableVoices.length);
        return { status: "ready", mode: currentMode, voicesCount: availableVoices.length };
    } catch (error) {
        console.error("Помилка ініціалізації AI:", error);
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
        const result = await stressClient.predict(stressEndpoint, [text]);
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
        mode: currentMode || getMode(),
        ttsClientInitialized: !!ttsClient,
        stressClientInitialized: !!stressClient,
        voicesCount: availableVoices.length,
        hasAccessToken: !!process.env.HF_TOKEN,
        localTtsUrl: process.env.LOCAL_TTS_URL || null,
        localStressUrl: process.env.LOCAL_STRESS_URL || null,
    };
}

module.exports = { initAI, generateAudio, getRandomVoice, getStatus };
