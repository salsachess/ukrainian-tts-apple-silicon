require('dotenv').config();
const express = require('express');
const cors = require('cors');
const db = require('./db');
const ai = require('./ai_client');

const app = express();
app.use(cors());
app.use(express.json());

// Ендпоінт для кнопки «Прогрів» на Frontend
app.post('/api/pre-warm', async (req, res) => {
    try {
        const status = await ai.initAI();
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
            voiceId = ai.getRandomVoice(); // Новий персонаж — призначаємо випадковий голос
            db.run("INSERT INTO characters (name, voice_id) VALUES (?, ?)", [character, voiceId]);
        }

        try {
            const audioResult = await ai.generateAudio(text, voiceId);

            // Завантажуємо аудіо як ArrayBuffer і відправляємо на Frontend
            let audioUrl = audioResult.url || audioResult;
            if (typeof audioResult === 'object' && audioResult.path) {
                 // in some cases gradio client returns {path: '...', url: '...'}
                 audioUrl = audioResult.url;
            }
            
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();

            res.setHeader('Content-Type', 'audio/wav');
            res.send(Buffer.from(arrayBuffer));

        } catch (error) {
            console.error("Detailed error in TTS:", error);
            let userFriendlyError = "Помилка генерації аудіо";
            
            // Convert error to string to check its contents
            const errorStr = typeof error === 'object' ? JSON.stringify(error) + (error.message || '') : String(error);
            
            if (errorStr.includes("ZeroGPU quota exceeded")) {
                userFriendlyError = "Вичерпано ліміт безкоштовного використання AI (ZeroGPU quota exceeded).";
                const match = errorStr.match(/Try again in ([\d:]+)/);
                if (match) {
                    userFriendlyError += ` Зачекайте ${match[1]} і спробуйте знову.`;
                }
            }

            res.status(500).json({ error: userFriendlyError, details: error.message || errorStr });
        }
    });
});

// Ендпоінт статусу системи
app.get('/api/status', async (req, res) => {
    try {
        const aiStatus = ai.getStatus();
        
        db.all("SELECT name, voice_id FROM characters ORDER BY name", [], (err, rows) => {
            if (err) {
                return res.status(500).json({ error: "Помилка БД", details: err.message });
            }
            
            // Формуємо маппінг персонаж → голос
            const characterMapping = {};
            (rows || []).forEach(row => {
                characterMapping[row.name] = row.voice_id;
            });

            res.json({
                status: "ok",
                timestamp: new Date().toISOString(),
                ai: aiStatus,
                database: {
                    charactersCount: (rows || []).length,
                    characterMapping
                }
            });
        });
    } catch (error) {
        res.status(500).json({ error: "Помилка отримання статусу", details: error.message });
    }
});

// =========================================================================
// OpenAI-сумісний міст (для Social Stream Ninja та інших клієнтів)
// =========================================================================
app.post('/v1/audio/speech', async (req, res) => {
    try {
        const { input, voice } = req.body;
        
        if (!input) {
            return res.status(400).json({ error: { message: "Missing 'input' field.", type: "invalid_request_error" }});
        }
        
        // Розбір формату Social Stream Ninja: "salsachess! ! . вітаю..."
        let characterName = "Гість";
        let messageText = input;
        
        const separator = "! ! .";
        const separatorIndex = input.indexOf(separator);
        
        if (separatorIndex !== -1) {
            characterName = input.substring(0, separatorIndex).trim();
            messageText = input.substring(separatorIndex + separator.length).trim();
        }

        // Отримання або призначення голосу для персонажа
        const voiceId = await new Promise((resolve, reject) => {
            db.get("SELECT voice_id FROM characters WHERE name = ?", [characterName], (err, row) => {
                if (err) return reject(err);
                if (row) {
                    resolve(row.voice_id);
                } else {
                    const newVoiceId = ai.getRandomVoice();
                    db.run("INSERT INTO characters (name, voice_id) VALUES (?, ?)", [characterName, newVoiceId], (insertErr) => {
                        if (insertErr) return reject(insertErr);
                        resolve(newVoiceId);
                    });
                }
            });
        });

        // Генеруємо аудіо ТІЛЬКИ для тексту повідомлення
        console.log(`[OpenAI Bridge] RAW input: "${input}"`);
        console.log(`[OpenAI Bridge] User: ${characterName} | Voice: ${voiceId} | Text: ${messageText}`);
        const audioResult = await ai.generateAudio(messageText, voiceId);
        
        let audioUrl = audioResult.url || audioResult;
        if (typeof audioResult === 'object' && audioResult.path) {
             audioUrl = audioResult.url;
        }
            
        const response = await fetch(audioUrl);
        const arrayBuffer = await response.arrayBuffer();

        // OpenAI API повертає аудіо потік
        res.setHeader('Content-Type', 'audio/wav');
        res.send(Buffer.from(arrayBuffer));
    } catch (error) {
        console.error("OpenAI Emulation Error:", error);
        res.status(500).json({ error: { message: error.message }});
    }
});

const PORT = 3000;
const HOST = '0.0.0.0';

app.listen(PORT, HOST, () => {
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    let localIp = '127.0.0.1';
    
    // Знаходимо першу актуальну IPv4 адресу (не localhost)
    for (const interfaceName in networkInterfaces) {
        const interfaces = networkInterfaces[interfaceName];
        for (const iface of interfaces) {
            if (iface.family === 'IPv4' && !iface.internal) {
                localIp = iface.address;
                break;
            }
        }
        if (localIp !== '127.0.0.1') break;
    }

    const mode = process.env.TTS_MODE || 'huggingface';
    console.log(`Бекенд запущено`);
    console.log(`  - Local: http://localhost:${PORT}`);
    console.log(`  - LAN:   http://${localIp}:${PORT}`);
    console.log(`Режим генерації: ${mode.toUpperCase()}`);
    console.log(`OpenAI Bridge: http://${localIp}:${PORT}/v1/audio/speech`);
    console.log(`Натисни "Прогрів" на клієнті перед початком стріму.`);
});
