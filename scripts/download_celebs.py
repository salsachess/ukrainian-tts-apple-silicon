import os
import requests
from huggingface_hub import HfApi

def download_file(url, filename):
    print(f"Завантажую {filename}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(os.path.join("temp_voices", filename), 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Успішно: {filename}")
    except Exception as e:
        print(f"❌ Помилка завантаження {filename}: {e}")

def main():
    os.makedirs("temp_voices", exist_ok=True)
    
    # Прямі посилання на чисті аудіо-файли з різних відкритих джерел/датасетів
    voices = {
        # Часто використовувані тестові семпли
        "morgan_freeman.wav": "https://huggingface.co/datasets/elevenlabs/voices/resolve/main/morgan_freeman.wav", # Приклад структури, спробуємо кілька варіантів
        "trump_speech.wav": "https://huggingface.co/datasets/Matthijs/cmu-arctic-xvectors/resolve/main/cmu_us_awb_arctic/wav/arctic_a0001.wav", # Просто тестовий чоловічий голос, якщо Трамп не знайдеться
    }
    
    # Використаємо надійні відкриті посилання на публічні промови
    # Для Трампа (офіційний архів Білого Дому / публічне надбання)
    voices["donald_trump.mp3"] = "https://upload.wikimedia.org/wikipedia/commons/4/4e/President_Trump_Remarks_to_the_UN_General_Assembly.mp3"
    
    # Для Зеленського (публічне надбання, звернення до Конгресу)
    voices["zelenskyy.mp3"] = "https://upload.wikimedia.org/wikipedia/commons/e/ec/Volodymyr_Zelenskyy_addresses_the_US_Congress_%28March_16%2C_2022%29.webm" # Завантажимо аудіо/відео і витягнемо звук
    
    # Для Барака Обами
    voices["obama.mp3"] = "https://upload.wikimedia.org/wikipedia/commons/8/8c/Barack_Obama_Victory_Speech_2008.ogg"
    
    # Для Моргана Фрімена спробуємо знайти надійний лінк або візьмемо тестовий "голос диктора"
    
    for filename, url in voices.items():
        download_file(url, filename)

if __name__ == "__main__":
    main()
