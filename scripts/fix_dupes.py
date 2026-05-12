import sqlite3
import glob
import os
import random

def main():
    db_path = 'backend/characters.sqlite'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Отримуємо всі доступні кастомні голоси
    available_voices = [os.path.basename(f).replace('.pt', '') for f in glob.glob('custom_voices/*.pt')]
    
    # Отримуємо всі голоси, які зараз зайняті (щоб знайти вільні)
    c.execute("SELECT DISTINCT voice_id FROM characters")
    used_voices = [row[0] for row in c.fetchall()]
    
    unused_voices = list(set(available_voices) - set(used_voices))
    # Перемішаємо, щоб видавати випадково
    random.shuffle(unused_voices)

    # Знаходимо всі голоси з дублікатами (крім сальсачеса)
    c.execute('''
        SELECT voice_id 
        FROM characters 
        WHERE voice_id != 'сальсачес-піднесений' 
        GROUP BY voice_id 
        HAVING COUNT(*) > 1
    ''')
    duplicate_voice_ids = [row[0] for row in c.fetchall()]

    if not duplicate_voice_ids:
        print("Дублікатів не знайдено.")
        return

    changes_made = 0

    for v_id in duplicate_voice_ids:
        # Отримуємо всіх користувачів з цим голосом, відсортованих за ID (перший створений - перший у списку)
        c.execute("SELECT id, name FROM characters WHERE voice_id = ? ORDER BY id ASC", (v_id,))
        users = c.fetchall()
        
        # Першого залишаємо, інших змінюємо
        first_user = users[0]
        duplicates = users[1:]
        
        print(f"\nГолос '{v_id}': залишаємо за {first_user[1]}")
        
        for dup in duplicates:
            if not unused_voices:
                print("❌ Не вистачає вільних голосів для розподілу!")
                break
                
            new_voice = unused_voices.pop()
            c.execute("UPDATE characters SET voice_id = ? WHERE id = ?", (new_voice, dup[0]))
            print(f"  -> {dup[1]} отримує новий унікальний голос: {new_voice}")
            changes_made += 1

    conn.commit()
    conn.close()
    
    print(f"\n✅ Готово! Успішно оновлено {changes_made} користувачів.")

if __name__ == '__main__':
    main()
