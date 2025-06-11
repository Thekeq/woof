from db import DataBase

db = DataBase("data.db")

# Задания с вручную заданными ID
inviteItemsData = {
    'limited': [
    ],
    'in-game': [
        {
            'id': 1,
            'icon': '/static/media/telegram.svg',
            'description': 'Follow channel',
            'reward': 500,
            'onclick': "subscribeToTelegram({{userId}})"
        },
        {
            'id': 2,
            'icon': '/static/media/check.svg',
            'description': 'Daily check-in',
            'reward': 500,
            'onclick': "checkin({{userId}})"
        },
        {
            'id': 15,
            'icon': '/static/media/boost.png',
            'description': 'Boost WOOFS channel',
            'reward': 5000,
            'onclick': "boostChannel({{userId}}, 'https://t.me/boost/woofsupfam', 15)"
        },
        {
            'id': 3,
            'icon': '/static/media/premium.svg',
            'description': 'Telegram Premium',
            'reward': 2500,
            'onclick': "user_premium({{userId}})"
        },
        {
            'id': 4,
            'icon': '/static/media/invitefren.svg',
            'description': 'Invite 10 friends',
            'reward': 10000,
            'onclick': "user_friends({{userId}})"
        },
        {
            'id': 8,
            'icon': '/static/media/invitefren.svg',
            'description': 'Invite 3 frens',
            'reward': 5000,
            'onclick': "invite_fren_limit({{userId}}, 3, 8)"
        },
        {
            'id': 14,
            'icon': '/static/media/invitefren.svg',
            'description': 'Invite 1 frens',
            'reward': 1000,
            'onclick': "invite_fren_limit({{userId}}, 1, 14)"
        },
    ],
    'partners': [
    ]
}

# Очищаем таблицу перед добавлением новых данных
db.cursor.execute('DELETE FROM tasks')
db.cursor.execute('DELETE FROM sqlite_sequence WHERE name="tasks"')  # Сбрасываем автоинкремент ID
db.connection.commit()

# Добавляем задания через методы класса DataBase
for task_type, tasks in inviteItemsData.items():
    for task in tasks:
        db.cursor.execute('''
            INSERT INTO tasks (id, type, description, reward, action, icon)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task['id'], task_type, task['description'], task['reward'], task['onclick'], task['icon']))

db.connection.commit()
print("Задания успешно добавлены в базу данных!")
