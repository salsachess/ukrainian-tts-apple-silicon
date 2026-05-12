import os
import glob
import subprocess
import random

# Парсимо файл з іменами
speakers = {}
with open('librispeech/SPEAKERS.TXT', 'r') as f:
    for line in f:
        if line.startswith(';'): continue
        parts = line.strip().split('|')
        if len(parts) >= 5:
            spk_id = parts[0].strip()
            gender = parts[1].strip()
            name = parts[4].strip()
            speakers[spk_id] = {'gender': gender, 'name': name}

base_dir = 'librispeech/dev-clean'
males = []
females = []

# Знаходимо всіх доступних дикторів
for spk_id in os.listdir(base_dir):
    if spk_id in speakers:
        if speakers[spk_id]['gender'] == 'M':
            males.append(spk_id)
        else:
            females.append(spk_id)

# Перебираємо ВСІХ дикторів
for spk_id in males + females:
    info = speakers[spk_id]
    safe_name = info['name'].replace(' ', '_')
    pt_file = f"{safe_name}.pt"
    custom_pt_file = f"custom_voices/{pt_file}"
    
    # Пропускаємо, якщо голос вже додано
    if os.path.exists(custom_pt_file) or os.path.exists(pt_file):
        print(f"⏩ Пропускаємо {safe_name} (вже існує)")
        continue
        
    # Знаходимо будь-який flac файл для цього диктора
    flac_files = glob.glob(f'{base_dir}/{spk_id}/**/*.flac', recursive=True)
    
    if flac_files:
        sample_file = flac_files[0]
        print(f"Клоную голос: {safe_name} ({info['gender']}) з файлу {sample_file}")
        
        # Запускаємо процес клонування
        cmd = ['scripts/.venv/bin/python3', 'scripts/clone_voice.py', sample_file, safe_name]
        try:
            subprocess.run(cmd, check=True)
            if os.path.exists(pt_file):
                os.rename(pt_file, custom_pt_file)
                print(f"✅ Успішно додано: {custom_pt_file}")
        except Exception as e:
            print(f"❌ Помилка під час клонування {safe_name}: {e}")
