import json
import sqlite3
import time
from datetime import datetime, timedelta


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        # Создание таблицы, если она еще не существует
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    referrer_id INTEGER,
                    balance INTEGER DEFAULT 0,
                    friends_count INTEGER DEFAULT 0,
                    friends_list TEXT,
                    friends_id TEXT,
                    friends_time TEXT,
                    checkin INTEGER DEFAULT 0,
                    rewards TEXT,
                    username TEXT
                )
            ''')
        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS transactions (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            transaction_id TEXT UNIQUE
                        )
                    ''')
        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            type TEXT,
                            description TEXT,
                            reward INTEGER,
                            action TEXT,
                            icon TEXT
                        )
                    ''')
        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_tasks (
                            id INTEGER,
                            user_id INTEGER,
                            task_id INTEGER,
                            completed BOOLEAN,
                            completion_time TIMESTAMP
                        )
                    ''')

        self.connection.commit()

    def add_friend_id(self, user_id, friend_id):
        with self.connection:
            # Получаем текущий список друзей пользователя
            self.cursor.execute(
                "SELECT `friends_id` FROM `users` WHERE `user_id` = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()
            if result:
                current_friends_list = result[0]
            else:
                current_friends_list = ""

            # Добавляем нового друга к текущему списку друзей
            if current_friends_list:
                updated_friends_list = current_friends_list + f",{friend_id}"
            else:
                updated_friends_list = str(friend_id)

            # Обновляем запись в базе данных с новым списком друзей
            self.cursor.execute(
                "UPDATE `users` SET `friends_id` = ? WHERE `user_id` = ?",
                (updated_friends_list, user_id)
            )

    def add_frens_count(self, user_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `users` SET `friends_count` = `friends_count` + ? WHERE `user_id` = ?",
                (1, user_id)
            )

    def add_friend(self, user_id, friend_id):
        with self.connection:
            # Получаем текущий список друзей пользователя
            self.cursor.execute(
                "SELECT `friends_list` FROM `users` WHERE `user_id` = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()
            if result:
                current_friends_list = result[0]
            else:
                current_friends_list = ""

            # Добавляем нового друга к текущему списку друзей
            if current_friends_list:
                updated_friends_list = current_friends_list + f",{friend_id}"
            else:
                updated_friends_list = str(friend_id)

            self.cursor.execute(
                "SELECT `friends_time` FROM `users` WHERE `user_id` = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()
            if result:
                current_friends_time = result[0]
            else:
                current_friends_time = ""

            # Добавляем нового друга к текущему списку друзей
            if current_friends_time:
                updated_friends_time = current_friends_time + f",{time.time()}"
            else:
                updated_friends_time = str(time.time())

            # Обновляем запись в базе данных с новым списком друзей
            self.cursor.execute(
                "UPDATE `users` SET `friends_list` = ? WHERE `user_id` = ?",
                (updated_friends_list, user_id)
            )
            self.cursor.execute(
                "UPDATE `users` SET `friends_time` = ? WHERE `user_id` = ?",
                (updated_friends_time, user_id)
            )

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id, username, referrer_id=None):
        with self.connection:
            if referrer_id is not None:
                self.cursor.execute(
                    "INSERT INTO `users` (`user_id`, `username`, `referrer_id`) VALUES (?, ?, ?)",
                    (user_id, username, referrer_id)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO `users` (`user_id`, `username`) VALUES (?, ?)",
                    (user_id, username)
                )

    def add_transaction(self, user_id, transaction):
        with self.connection:
            return self.cursor.execute("INSERT INTO `transactions` (`user_id`, `transaction_id`) VALUES (?, ?)",
                                       (user_id, transaction))

    def get_transaction(self, transaction_id):
        with self.connection:
            transaction = self.cursor.execute("SELECT * FROM `transactions` WHERE `transaction_id` = ?",
                                              (transaction_id,)).fetchone()
            return transaction is not None

    def add_balance(self, user_id, coin):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `users` SET `balance` = `balance` + ? WHERE `user_id` = ?",
                (coin, user_id)
            )

    def set_balance(self, user_id, coin):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `users` SET `balance` = ? WHERE `user_id` = ?",
                (coin, user_id)
            )

    def user_balance(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `balance` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchone()
            return result[0]

    def user_wallet(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `wallet_address` FROM `users` WHERE `user_id` = ?",
                                         (user_id,)).fetchone()
            return result[0]

    def get_all_users(self):
        with self.connection:
            result = self.cursor.execute("SELECT `user_id` FROM `users`").fetchall()
            return [row[0] for row in result]

    def get_user_count(self):
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(`user_id`) FROM `users`").fetchone()
            return result[0] if result else 0

    def is_task_completed(self, user_id, task_id):
        result = self.cursor.execute('''
            SELECT completed FROM user_tasks
            WHERE user_id = ? AND task_id = ?
        ''', (user_id, task_id)).fetchone()
        return result is not None and result[0] == 1

    def complete_task(self, user_id, task_id):
        # Проверяем, существует ли запись с таким user_id и task_id
        self.cursor.execute('''
            SELECT id FROM user_tasks WHERE user_id = ? AND task_id = ?
        ''', (user_id, task_id))
        result = self.cursor.fetchone()

        if result:
            # Если запись существует, обновляем только completion_time
            self.cursor.execute('''
                UPDATE user_tasks
                SET completed = ?, completion_time = ?
                WHERE user_id = ? AND task_id = ?
            ''', (True, time.time(), user_id, task_id))
        else:
            # Если записи нет, вставляем новую
            self.cursor.execute('''
                INSERT INTO user_tasks (user_id, task_id, completed, completion_time)
                VALUES (?, ?, ?, ?)
            ''', (user_id, task_id, True, time.time()))

        self.connection.commit()

    def get_available_tasks(self):
        return self.cursor.execute('SELECT * FROM tasks').fetchall()

    def get_completion_time(self, user_id, task_id):
        result = self.cursor.execute('''
            SELECT completion_time FROM user_tasks
            WHERE user_id = ? AND task_id = ?
        ''', (user_id, task_id)).fetchone()

        if result:
            return result[0]
        else:
            return False

    def get_user(self, user_id):
        with self.connection:
            info = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?",
                                       (user_id,)).fetchone()
            return info

    import json  # Подключаем модуль для работы с JSON

    # Получение rewards как Python-словаря
    def get_rewards(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `rewards` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchone()
            if result and result[0]:  # Если данные существуют
                try:
                    return json.loads(result[0])  # Преобразуем JSON-строку в словарь
                except json.JSONDecodeError:
                    print(f"Invalid JSON format for user_id={user_id}: {result[0]}")
                    return {}  # Возвращаем пустой словарь
            return {}  # Если данных нет, возвращаем пустой словарь

    # Обновление rewards
    def update_rewards(self, user_id, rewards_dict):
        with self.connection:
            rewards_json = json.dumps(rewards_dict)  # Преобразуем словарь в JSON-строку
            self.cursor.execute("UPDATE `users` SET `rewards` = ? WHERE `user_id` = ?", (rewards_json, user_id))

    def update_checkin(self, user_id):
        with self.connection:
            self.cursor.execute("UPDATE `users` SET `checkin` = `checkin` + 1 WHERE `user_id` = ?", (user_id,))

    def get_leaderboard(self, limit=100, offset=0):
        """Получить список лидеров, отсортированных по балансу."""
        with self.connection:
            result = self.cursor.execute(
                "SELECT username, balance FROM users ORDER BY balance DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [{"username": row[0], "balance": row[1]} for row in result]

    def get_user_leaderboard(self, user_id):
        """Получить список лидеров, отсортированных по балансу."""
        with self.connection:
            result = self.cursor.execute(
                """
                SELECT `username`, `balance`
                FROM `users`
                WHERE `user_id` = ?
                """,
                (user_id,)
            ).fetchall()
            return [{"username": row[0], "balance": row[1]} for row in result]


    def get_user_position(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                """
                SELECT COUNT(*) + 1 FROM `users`
                WHERE `balance` > (SELECT `balance` FROM `users` WHERE `user_id` = ?)
                """,
                (user_id,)
            ).fetchone()
            return result[0] if result else None

    def get_user_checkin(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `checkin` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchone()
            return result[0] if result else 0

    def get_task_amount(self, id):
        with self.connection:
            result = self.cursor.execute("SELECT `reward` FROM `tasks` WHERE `id` = ?", (id,)).fetchone()
            return result[0] if result else 0
