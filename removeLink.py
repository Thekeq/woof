import sqlite3
import re

# Подключение к базе данных
db_name = "data.db"  # Укажите имя вашей базы данных
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# ID пользователя, у которого нужно изменить username
user_id = 5587645898

# Функция для удаления ссылки из строки
def remove_link(username):
    # Регулярное выражение для поиска URL
    url_pattern = r"https?://[^\s]+"
    # Удаление всех URL из строки
    return re.sub(url_pattern, "", username).strip()

# Получение текущего username пользователя
cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
result = cursor.fetchone()

if result:
    current_username = result[0]
    # Очистка username от ссылки
    new_username = remove_link(current_username)

    # Обновление username в базе данных
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (new_username, user_id))
    conn.commit()

    print(f"Имя пользователя успешно обновлено на: {new_username}")
else:
    print(f"Пользователь с user_id {user_id} не найден.")

# Закрытие соединения
conn.close()
