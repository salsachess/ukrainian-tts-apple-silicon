import os
import glob
import subprocess
import librosa
import soundfile as sf

def improve_voice(name_to_fix):
    # Зчитуємо ID дикторів
    spk_id = None
    with open('librispeech/SPEAKERS.TXT', 'r') as f:
        for line in f:
            if line.startswith(';'): continue
            parts = line.strip().split('|')
            if len(parts) >= 5:
                name = parts[4].strip()
                safe_name = name.replace(' ', '_')
                if safe_name == name_to_fix:
                    spk_id = parts[0].strip()
                    break
    
    if not spk_id:
        print(f"❌ Не знайдено ID для {name_to_fix}")
        return

    # Шукаємо всі flac файли
    base_dir = 'librispeech/dev-clean'
    flac_files = glob.glob(f'{base_dir}/{spk_id}/**/*.flac', recursive=True)
    
    if not flac_files:
        print(f"❌ Не знайдено аудіо для {name_to_fix}")
        return
        
    # Беремо файл (бажано не перший, щоб був інший семпл)
    sample_file = flac_files[1] if len(flac_files) > 1 else flac_files[0]
    
    print(f"\nОбробка {name_to_fix} з {sample_file}...")
    
    # 1. Завантажуємо файл
    y, sr = librosa.load(sample_file, sr=24000)
    
    # 2. Обрізаємо тишу на початку і в кінці (top_db=30 означає тихіше ніж 30дБ від піку вважається тишею)
    y_trimmed, _ = librosa.effects.trim(y, top_db=30)
    
    # 3. Беремо рівно 8 секунд
    target_len = sr * 8
    if len(y_trimmed) > target_len:
        y_final = y_trimmed[:target_len]
    else:
        y_final = y_trimmed # Якщо коротше 8с - беремо як є
        
    # Зберігаємо тимчасовий покращений файл
    tmp_wav = f"temp_{name_to_fix}.wav"
    sf.write(tmp_wav, y_final, sr)
    
    # 4. Запускаємо клонування
    cmd = ['scripts/.venv/bin/python3', 'scripts/clone_voice.py', tmp_wav, name_to_fix]
    try:
        subprocess.run(cmd, check=True)
        pt_file = f"{name_to_fix}.pt"
        if os.path.exists(pt_file):
            os.rename(pt_file, f"custom_voices/{pt_file}")
            print(f"✅ Успішно оновлено: {name_to_fix}")
    except Exception as e:
        print(f"❌ Помилка під час клонування {name_to_fix}: {e}")
        
    # Прибираємо тимчасовий файл
    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)

def main():
    voices_to_fix = [
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
    
    for voice in voices_to_fix:
        # Спочатку видаляємо старий глючний .pt файл, якщо він там є
        old_file = f"custom_voices/{voice}.pt"
        if os.path.exists(old_file):
            os.remove(old_file)
            
        improve_voice(voice)

if __name__ == "__main__":
    main()
