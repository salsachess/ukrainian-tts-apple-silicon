import torch
import sys
import os
from styletts2_inference.models import StyleTTS2

def clone_voice(audio_path, output_name):
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"

    print(f"Завантаження моделі на пристрій: {device}...")
    model = StyleTTS2(hf_path="patriotyk/styletts2_ukrainian_multispeaker_hifigan", device=device)
    
    print(f"Вилучення характеристик голосу з: {audio_path}...")
    try:
        features = model.extract_voice_features(audio_path)
        
        # Створюємо директорію, якщо її немає
        # Але ми зазвичай хочемо додати це до вже існуючих голосів
        output_path = f"{output_name}.pt"
        torch.save(features, output_path)
        print(f"Успіх! Голос збережено у файл: {output_path}")
        print("Тепер ви можете перемістити цей файл у папку з голосами.")
    except Exception as e:
        print(f"Помилка при клонуванні: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Використання: python clone_voice.py <шлях_до_аудіо> <ім'я_голосу>")
    else:
        clone_voice(sys.argv[1], sys.argv[2])
