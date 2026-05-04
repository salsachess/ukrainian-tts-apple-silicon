import os
import torch
import gradio as gr
import numpy as np
from huggingface_hub import snapshot_download
from styletts2_inference.models import StyleTTS2
import re
from unicodedata import normalize
from ipa_uk import ipa
from ukrainian_word_stress import Stressifier, StressSymbol

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

def verbalize(text: str) -> str:
    return text

def synthesize(model_name: str, text: str, speed: float = 1.0, voice_name: str = "Тетяна Гончарова"):
    if model_name == "multi": model = model_multi
    else: model = model_single
    if model is None: raise gr.Error("Model not loaded")
    
    try:
        clean_text = text.strip()
        clean_text = clean_text.replace('"', '')
        if clean_text:
            clean_text = clean_text.replace('+', StressSymbol.CombiningAcuteAccent)
            clean_text = normalize('NFKC', clean_text)
            clean_text = re.sub(r'[᠆‐‑‒–—―⁻₋−⸺⸻]', '-', clean_text)
            if clean_text[-1] not in '.?!:-':
                clean_text += '.'
            clean_text = re.sub(r' - ', ': ', clean_text)
            clean_text = stressify(clean_text)
            ps = ipa(clean_text)
        else:
            raise ValueError("Empty text")

        print(f"[TTS] Фонетизація (IPA_UK): {ps[:60]}...")
        tokens = model.tokenizer.encode(ps)
        
        style = None
        if model_name == "multi":
            # Спочатку шукаємо в кастомних голосах
            custom_style_path = os.path.join(CUSTOM_VOICES_DIR, f"{voice_name}.pt")
            if os.path.exists(custom_style_path):
                print(f"[TTS] Використовується кастомний голос: {voice_name}")
                style = torch.load(custom_style_path, map_location=DEVICE)
            elif voices_dir:
                # Потім у стандартних
                style_path = os.path.join(voices_dir, f"{voice_name}.pt")
                if os.path.exists(style_path):
                    style = torch.load(style_path, map_location=DEVICE)
            
            if style is not None and style.ndim == 1:
                style = style.unsqueeze(0)
        
        if style is None:
            # Для unknown voice або single моделі застосовуємо дифузію
            print("[TTS] Дифузія просодії (single model)...")
            with torch.no_grad():
                style = model.predict_style_single(torch.LongTensor(tokens).to(DEVICE), diffusion_steps=30, embedding_scale=1.5)
            
        with torch.no_grad():
            t = torch.LongTensor(tokens).to(DEVICE)
            s = style.to(DEVICE)
            wav = model(t, s_prev=s, speed=speed)
            
        if isinstance(wav, torch.Tensor): wav = wav.cpu().numpy()
        wav = np.squeeze(wav)
        return (24000, wav)
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
