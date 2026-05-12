import librosa
import soundfile as sf
import os
import glob

def trim_audio(filepath, duration=10.0):
    print(f"Обрізаю {filepath} до {duration} секунд...")
    try:
        # Завантажуємо лише перші 10 секунд
        y, sr = librosa.load(filepath, sr=24000, duration=duration)
        
        # Створюємо нове ім'я файлу
        base, ext = os.path.splitext(filepath)
        new_filepath = f"{base}_short.wav"
        
        # Зберігаємо короткий файл
        sf.write(new_filepath, y, sr)
        print(f"✅ Успішно збережено: {new_filepath}")
        return new_filepath
    except Exception as e:
        print(f"❌ Помилка обробки {filepath}: {e}")
        return None

def main():
    # Беремо наші гігантські файли
    files = ["temp_voices/donald_trump.wav", "temp_voices/zelenskyy.wav", "temp_voices/morgan_freeman.wav"]
    
    for f in files:
        if os.path.exists(f):
            trim_audio(f)
        else:
            print(f"⚠️ Файл не знайдено: {f}")

if __name__ == "__main__":
    main()
