import os
import glob
import time
from gradio_client import Client

def main():
    # Створюємо папку для тестів
    os.makedirs('test_outputs', exist_ok=True)
    
    # Підключаємося до нашого локального TTS сервера
    try:
        client = Client("http://127.0.0.1:7860/")
    except Exception as e:
        print(f"Помилка підключення до сервера TTS: {e}")
        print("Переконайтеся, що сервер (.vv) запущено.")
        return

    # Знаходимо всі голоси
    voices_to_test = [
        "David_Mecionis",
        "E._Tavano",
        "Jean_Bascom",
        "JudyGibson",
        "Nicodemus",
        "Winston_Tharp",
        "Renata",
        "Scott_Walter",
        "VOICEGUY"
    ]
    text = "Привіт, це тест мого голосу. Перевіряємо якість звуку та наявність відлуння."
    
    print(f"Починаю генерацію тестів для {len(voices_to_test)} голосів...")
    
    for voice_name in voices_to_test:
        out_path = f"test_outputs/{voice_name}.wav"
        
        # Видаляємо старий файл, якщо він є
        if os.path.exists(out_path):
            os.remove(out_path)
            
        print(f"Генерую: {voice_name}...")
        try:
            # Викликаємо функцію TTS
            result = client.predict(
                "multi", # model_choice
                text, # text_input
                1.0, # speed
                voice_name, # voice
                api_name="/synthesize"
            )
            
            # Gradio повертає шлях до тимчасового файлу, переміщуємо його
            if isinstance(result, str) and os.path.exists(result):
                os.rename(result, out_path)
            elif isinstance(result, tuple) and os.path.exists(result[0]):
                os.rename(result[0], out_path)
                
        except Exception as e:
            print(f"❌ Помилка для {voice_name}: {e}")
            
    print("\n✅ Всі тести згенеровано в папку 'test_outputs'!")

if __name__ == "__main__":
    main()
