import os
import torch
import gradio as gr
import numpy as np
from scipy import signal as scipy_signal
from huggingface_hub import snapshot_download
from styletts2_inference.models import StyleTTS2
import re
from unicodedata import normalize
from ipa_uk import ipa
from ukrainian_word_stress import Stressifier, StressSymbol
from num2words import num2words

# NLTK setup
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

DEVICE = "cpu"
MODEL_MULTI_REPO = "patriotyk/styletts2_ukrainian_multispeaker_hifigan"
MODEL_SINGLE_REPO = "patriotyk/styletts2_ukrainian_single"
VOICES_REPO = "patriotyk/styletts2-ukrainian"

model_multi = None
model_single = None
voices_dir = None
CUSTOM_VOICES_DIR = "/Users/serhiy.franchuk/Documents/working/voices-on-the-stream/custom_voices"

stressify = Stressifier()

def load_models():
    global model_multi, model_single, voices_dir
    print(f"[TTS] Loading multispeaker model {MODEL_MULTI_REPO}...")
    model_multi = StyleTTS2(hf_path=MODEL_MULTI_REPO, device=DEVICE)
    voices_path = snapshot_download(repo_id=VOICES_REPO, repo_type="space", allow_patterns="voices/*.pt")
    voices_dir = os.path.join(voices_path, "voices")
    print(f"[TTS] Loading single speaker model...")
    model_single = StyleTTS2(hf_path=MODEL_SINGLE_REPO, device=DEVICE)

load_models()

VOICES = [
    'Інна Гелевера', 'Анастасія Павленко', 'Артем Окороков', 'Вʼячеслав Дудко', 
    'Вероніка Дорош', 'Влада Муравець', 'Вікторія Левченко', 'Гаська Шиян', 
    'Денис Денисенко', 'Катерина Потапенко', 'Кирило Татарченко', 'Людмила Чиркова', 
    'Марина Панас', 'Марися Нікітюк', 'Марта Мольфар', 'Марічка Штирбулова', 
    'Матвій Ніколаєв', 'Михайло Тишин', 'Олександр Ролдугін', 'Олена Шверк', 
    'Павло Буковський', 'Петро Філяк', 'Поліна Еккерт(хлопчик)', 'Поліна Еккерт', 
    'Роман Куліш', 'Слава Красовська', 'Тарас Василюк', 'Тетяна Гончарова', 
    'Тетяна Лукинюк', 'Юрій Вихованець', 'Юрій Кудрявець'
]

# Список голосів тепер включає і локальні
def get_available_voices():
    voices = list(VOICES)
    if os.path.exists(CUSTOM_VOICES_DIR):
        for f in os.listdir(CUSTOM_VOICES_DIR):
            if f.endswith(".pt"):
                v_name = f[:-3]
                if v_name not in voices:
                    voices.append(v_name)
    return voices


EMOJI_MAP = {
    ":)": "посмішка", ":-)": "посмішка", ":(": "сум", ":-(": "сум",
    ";)": "підмигування", ";-)": "підмигування", ":D": "сміх", "XD": "сміх",
    "❤️": "серце", "😂": "регіт", "😊": "щасливе обличчя", "👍": "лайк",
    "🔥": "вогонь", "🙏": "дякую", "✨": "блискітки", "😭": "плач",
    "😎": "круто", "🤔": "хм", "😍": "закоханість", "🤣": "регіт",
    "🙌": "ура", "🤩": "вау", "🥳": "свято", "😢": "сльоза",
    "😡": "злість", "👏": "аплодисменти", "💯": "на всі сто",
    "🚀": "ракета", "🇺🇦": "Слава Україні", "💪": "сила",
    "👀": "очі", "👌": "окей", "🎉": "свято", "🎁": "подарунок",
    "💡": "ідея", "💥": "бум", "🤙": "на звязку", "👋": "привіт",
    "🤝": "згода", "🤯": "шок", "😇": "ангел", "😈": "бісеня",
    "💀": "череп", "🤡": "клоун", "👾": "монстрик", "🤖": "робот",
    # Twitch Custom Emojis (salsac)
    ":salsacSmile:": "посмішка", ":salsacPixel:": "піксель", ":salsacTake:": "таке собі",
    ":salsacNprmn:": "неприємно", ":salsacThumbsUp:": "клас", ":salsacCool:": "круто",
    ":salsacScream:": "крик", ":salsacSad:": "сумно", ":salsacAnime:": "аніме",
    ":salsacGrandpa:": "дідусь", ":salsacHaiky:": "ГАЙКИ", ":salsacThink:": "хм",
    ":salsacDance:": "танці", ":salsacRave:": "рейв", ":salsacCoolslide:": "крутезно",
    ":salsacSpin:": "кружляння", ":salsacShake:": "тряска", ":salsacTakeout:": "таке собі",
    ":salsacRain:": "дощ", ":salsacMadshake:": "злість", ":salsacUapawn:": "укропішак",
    ":salsacHeart:": "серце", ":salsacBunt:": "бунт"
}

ENGLISH_PHONETIC_MAP = {
    "the": "зе", "you": "ю", "your": "юр", "my": "май", "i": "ай",
    "love": "лав", "like": "лайк", "stream": "стрім", "hello": "геллоу",
    "hi": "хай", "thanks": "фенкс", "thank": "фенк", "good": "ґуд",
    "bad": "бед", "cool": "кул", "nice": "найс", "awesome": "осом",
    "great": "ґрейт", "game": "ґейм", "play": "плей", "watch": "вотч",
    "for": "фор", "with": "віз", "very": "вері", "much": "мач",
    "is": "із", "are": "ар", "am": "ем", "it": "іт", "this": "зіс",
    "that": "зет", "and": "енд", "to": "ту", "in": "ін", "on": "он",
    "of": "оф", "don't": "донт", "can't": "кант", "will": "віл", "be": "бі", "was": "воз", "a": "е",
    # Шахова та спортивна лексика
    "chess": "чес", "check": "чек", "mate": "мейт", "checkmate": "чекмейт",
    "pawn": "павн", "knight": "найт", "bishop": "бішоп", "rook": "рук",
    "queen": "квін", "king": "кінг", "move": "мув", "win": "він",
    "loss": "лосс", "draw": "дро", "blunder": "бландер", "brilliant": "брілліант",
    "puzzle": "пазл", "rating": "рейтинг", "elo": "ело", "bullet": "буллет",
    "blitz": "бліц", "rapid": "рапід", "score": "скор", "match": "матч",
    "player": "плеєр", "team": "тім", "coach": "коуч", "goal": "ґол",
    # Ніки та канали
    "salsachess": "сальсачес",
    "fso": "ефесо",
}

# Фонетичний словник абревіатур — застосовується ПІСЛЯ stressify
ABBREVIATION_MAP = {
    "упа": "упа́",
    "унр": "уене́р",
    "зсу": "зеесу́",
    "срср": "сирисири́",
    "фіде": "фіде́",
    "оун": "оуе́н",
    "сбу": "есбеу́",
    "нато": "нато́",
    "сша": "сша́",
    "оон": "оое́н",
    "ші": "ші́",
    # Ніки — виправляємо після stressify
    "сальсачес": "сальсаче́с",
    "ефесо": "ефесо́",
}

def apply_abbreviations(text: str) -> str:
    """Застосовуємо фонетичні наголоси для абревіатур."""
    for abbr, phonetic in ABBREVIATION_MAP.items():
        text = re.sub(re.escape(abbr), phonetic, text, flags=re.IGNORECASE)
    return text

def verbalize(text: str) -> str:
    # 0. Нормалізуємо текст (видаляємо приховані символи та варіації емодзі)
    text = normalize('NFKC', text)
    
    # 1. Заміна емодзі та смайликів
    for emoji_char, description in EMOJI_MAP.items():
        text = text.replace(emoji_char, f" {description} ")

    # 2. Англійський акцентолог
    words = text.split()
    processed_words = []
    for word in words:
        clean_word = word.lower().strip(".,!?\"'")
        if clean_word in ENGLISH_PHONETIC_MAP:
            new_word = word.lower().replace(clean_word, ENGLISH_PHONETIC_MAP[clean_word])
            processed_words.append(new_word)
        else:
            processed_words.append(word)
    text = " ".join(processed_words)

    # 3. Цифри → слова
    def replace_num(match):
        try:
            return num2words(int(match.group()), lang='uk')
        except:
            return match.group()
    text = re.sub(r'\d+', replace_num, text)
    return text

def synthesize(model_name: str, text: str, speed: float = 1.0, voice_name: str = "Тетяна Гончарова"):
    if model_name == "multi": model = model_multi
    else: model = model_single
    if model is None: raise gr.Error("Model not loaded")
    
    try:
        # 0. Видаляємо всі наявні наголоси, щоб почати з чистого аркуша
        text = text.replace('\u0301', '')
        
        # 1. Спершу обробляємо весь текст (емодзі та англійські слова)
        text = verbalize(text)
        # 2. Замінюємо абревіатури на фонетичні слова (УНР -> уене́р)
        text = apply_abbreviations(text)
        
        # 2. Розбиваємо текст на речення
        sentences = nltk.sent_tokenize(text)
        combined_wav = []
        
        for sentence in sentences:
            clean_text = sentence.strip()
            clean_text = clean_text.replace('"', '')
            if not clean_text: continue
            
            clean_text = clean_text.replace('+', StressSymbol.CombiningAcuteAccent)
            clean_text = normalize('NFKC', clean_text)
            clean_text = re.sub(r'[᠆‐‑‒–—―⁻₋−⸺⸻]', '-', clean_text)
            if clean_text[-1] not in '.?!:-':
                clean_text += '.'
            clean_text = stressify(clean_text)
            ps = ipa(clean_text)
            print(f"[TTS] {clean_text}")
            
            tokens = model.tokenizer.encode(ps)
            if len(tokens) > 510: tokens = tokens[:510]
            
            style = None
            if model_name == "multi":
                custom_style_path = os.path.join(CUSTOM_VOICES_DIR, f"{voice_name}.pt")
                if os.path.exists(custom_style_path):
                    print(f"[TTS] Loading CUSTOM voice: {custom_style_path}")
                    style = torch.load(custom_style_path, map_location=DEVICE)
                elif voices_dir:
                    style_path = os.path.join(voices_dir, f"{voice_name}.pt")
                    if os.path.exists(style_path):
                        print(f"[TTS] Loading builtin voice: {voice_name}")
                        style = torch.load(style_path, map_location=DEVICE)
                
                if style is None:
                    print(f"[TTS] WARNING: Voice '{voice_name}' NOT FOUND. Falling back to default.")

                if style is not None and style.ndim == 1:
                    style = style.unsqueeze(0)
                
                # Повертаємо легку емоційність (15% динаміки)
                if style is not None:
                    try:
                        with torch.no_grad():
                            text_style = model.predict_style_single(torch.LongTensor(tokens).to(DEVICE), diffusion_steps=50, embedding_scale=1.5)
                        
                        if not torch.isnan(text_style).any():
                            # ТИМЧАСОВО: 100% статики для тесту тембру
                            style = style.to(DEVICE)
                    except Exception:
                        pass
            
            if style is None:
                with torch.no_grad():
                    style = model.predict_style_single(torch.LongTensor(tokens).to(DEVICE), diffusion_steps=50, embedding_scale=1.5)
                
            with torch.no_grad():
                t = torch.LongTensor(tokens).to(DEVICE)
                s = style.to(DEVICE)
                # Додаткова фінальна перевірка стилю перед синтезом
                if torch.isnan(s).any():
                    raise ValueError("Неможливо згенерувати стиль для цього тексту (NaN).")
                wav = model(t, s_prev=s, speed=speed)
                
            if isinstance(wav, torch.Tensor): wav = wav.cpu().numpy()
            wav = np.squeeze(wav)
            
            # === САНІТАЙЗЕР АУДІО ===
            # Замінюємо NaN та Inf на 0 (тишу)
            wav = np.nan_to_num(wav, nan=0.0, posinf=0.0, neginf=0.0)
            # Обрізаємо пікові значення
            wav = np.clip(wav, -1.0, 1.0)
            
            # === LOW-PASS ФІЛЬТР (9кГц — звук стає прозорим) ===
            sos = scipy_signal.butter(6, 9000 / (24000 / 2), btype='low', output='sos')
            wav = scipy_signal.sosfiltfilt(sos, wav).astype(np.float32)
            
            # === ФЕЙД-ІН / ФЕЙД-АУТ ===
            # Плавно загасаємо кінець кожного речення (50мс при 24кГц = 1200 зразків)
            fade_samples = min(1200, len(wav) // 4)
            if fade_samples > 0:
                fade_out = np.linspace(1.0, 0.0, fade_samples)
                wav[-fade_samples:] *= fade_out
                fade_in = np.linspace(0.0, 1.0, fade_samples)
                wav[:fade_samples] *= fade_in
            
            # Невелика пауза між реченнями (100мс тиші)
            silence = np.zeros(int(24000 * 0.1), dtype=wav.dtype)
            combined_wav.append(wav)
            combined_wav.append(silence)

        if not combined_wav:
            raise ValueError("Empty text")
            
        final_wav = np.concatenate(combined_wav)
        
        # === ДИНАМІЧНИЙ ЛІМІТЕР (Захист від скреготу) ===
        # Якщо енергія сегмента занадто висока порівняно з середньою — притискаємо його
        rms_global = np.sqrt(np.mean(np.square(final_wav))) + 1e-6
        chunk_len = 1024
        threshold = 2.2 
        
        for i in range(0, len(final_wav), chunk_len):
            chunk = final_wav[i:i+chunk_len]
            if len(chunk) == 0: continue
            rms_local = np.sqrt(np.mean(np.square(chunk))) + 1e-6
            if rms_local > rms_global * threshold:
                gain = (rms_global * threshold) / rms_local
                final_wav[i:i+chunk_len] *= gain
        
        # Фінальна нормалізація гучності (пік = 0.90 для безпеки)
        peak = np.max(np.abs(final_wav))
        if peak > 0.01:
            final_wav = final_wav / peak * 0.90
        
        return (24000, final_wav)
    except Exception as e:
        print(f"[TTS] Error: {e}")
        raise gr.Error(str(e))

with gr.Blocks(title="StyleTTS2 Ukrainian") as demo:
    gr.Markdown("# 🇺🇦 StyleTTS2 Ukrainian")
    
    # Створюємо невидимий компонент для verbalize
    text_hidden = gr.Textbox(visible=False)
    verbalize_btn = gr.Button("Verbalize", visible=False)
    
    with gr.Row():
        with gr.Column():
            model_choice = gr.Radio(choices=["multi", "single"], value="multi", label="Model")
            text_input = gr.Textbox(label="Text", lines=3)
            voice_dropdown = gr.Dropdown(choices=get_available_voices(), value="Тетяна Гончарова", label="Voice")
            speed_slider = gr.Slider(minimum=0.5, maximum=2.0, value=1.0, label="Speed")
            synthesize_btn = gr.Button("🔊 Synthesize", variant="primary")
        with gr.Column():
            audio_output = gr.Audio(label="Result", type="numpy")
    
    synthesize_btn.click(fn=synthesize, inputs=[model_choice, text_input, speed_slider, voice_dropdown], outputs=[audio_output], api_name="synthesize")
    verbalize_btn.click(fn=verbalize, inputs=[text_input], outputs=[text_hidden], api_name="verbalize")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
