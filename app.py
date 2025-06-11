import asyncio
import hashlib
import os
import random
import secrets
import time
import urllib
import urllib.parse
from datetime import datetime, timedelta
from threading import Thread
from urllib.parse import parse_qs

import aiohttp
import jwt
from aiogram import Router, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, send_from_directory
from init_data_py import InitData
from db import DataBase
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
db = DataBase("data.db")

BOT_TOKEN = os.getenv("BOT_TOKEN")
app.secret_key = secrets.token_hex(32)
SECRET_KEY = hashlib.sha256(BOT_TOKEN.encode()).digest()
expected_secret_key = hashlib.sha256(f"{BOT_TOKEN}".encode()).digest()

import requests

CHANNEL_USERNAME = "woofsupfam"


def check_membership(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {
        "chat_id": f"@{CHANNEL_USERNAME}",
        "user_id": user_id
    }

    response = requests.get(url, params=params)
    data = response.json()

    if not data['ok']:
        print(f"Error: {data.get('description', 'Unknown error')}")
        return False

    # Проверяем статус и наличие is_premium
    result = data.get('result', {})
    user_info = result.get('user', {})

    if result.get('status') in ['member', 'administrator', 'creator']:
        is_premium = user_info.get('is_premium', False)  # Получаем is_premium с дефолтным значением False
        return is_premium  # Возвращаем True, если пользователь Premium

    return False


@app.route('/checkMembership', methods=['POST'])
def check_membership_route():
    data = request.json
    user_id = data['userId']

    if check_membership(user_id):
        return jsonify({'status': 'success', 'isMember': True})
    else:
        return jsonify({'status': 'fail', 'isMember': False})


def verify_access_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload  # Возвращаем полезную информацию (например, user_id)
    except jwt.ExpiredSignatureError:
        return None  # Токен истек
    except jwt.InvalidTokenError as e:
        return None  # Неверный токен


@app.route('/completeTask', methods=['POST'])
def complete_task():
    data = request.get_json()
    user_id = data.get('userId')
    task_id = data.get('task_id')
    amount = db.get_task_amount(task_id)
    print(amount)
    type = data.get('type', None)
    if db.is_task_completed(user_id, task_id) == False:
        if type is not None:
            # Обновляем rewards
            rewards = db.get_rewards(user_id)  # Получаем текущие rewards как словарь
            rewards[str(type)] = amount  # Добавляем или обновляем запись "Age"
            db.update_rewards(user_id, rewards)

        db.complete_task(user_id, task_id)
        db.add_balance(user_id, amount)
        return {"status": "success"}
    else:
        return {"status": "Already Completed"}


@app.route('/userInfo', methods=['GET'])
def get_user_info():
    user_id = request.args.get("userId")
    info = db.get_user(user_id)
    frens_ids = info[6].split(',') if info[6] else []  # Преобразуем строку с ID друзей в массив

    rewards = {}
    for fren_id in frens_ids:
        if fren_id.strip():
            fren_rewards = dict(db.get_rewards(fren_id))  # Получаем награды друга из базы
            rewards[fren_id] = fren_rewards

    result = {
        "id": info[0],
        "user_id": info[1],
        "referrer_id": info[2],
        "balance": info[3],
        "frens_count": info[4],
        "frens_list": info[5],
        "frens_id": info[6],
        "frens_time": info[7],
        "frens_rewards": rewards,
        "check-ins": info[8]
    }

    return jsonify(result)


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user_id = request.args.get("userId")
    tasks = db.get_available_tasks()

    result = []
    ids = [2]

    for task in tasks:
        task_id = task[0]
        action_with_user_id = task[4].replace('{{userId}}', str(user_id))
        task_data = {
            'id': task[0],
            'type': task[1],
            'description': task[2],  # Описание
            'reward': f"+{task[3]} WOOFS",  # Награда
            'onclick': action_with_user_id,  # Действие
            'icon': task[5]  # Иконка
        }
        if task_id in ids:
            if db.is_task_completed(user_id, task_id):
                completion_time = db.get_completion_time(user_id, task_id=task_id)
                next_available_time = datetime.fromtimestamp(completion_time) + timedelta(days=1)
                now = datetime.now()
                if next_available_time > now:
                    remaining_time = (next_available_time - now).total_seconds()
                    task_data['remaining_time'] = remaining_time
        else:
            if db.is_task_completed(user_id, task_id):
                task_data['completed'] = True

        result.append(task_data)
    return jsonify(result)


@app.route('/process_transaction', methods=['POST'])
async def process_transaction():
    data = request.get_json()  # Асинхронный парсинг JSON
    print(data)
    user_id = data.get('userId')
    msg_hash = data.get('msg_hash')
    amount = 500
    type = data.get('type')
    msg_hash = urllib.parse.quote(msg_hash)
    print(msg_hash)
    if not user_id or not msg_hash:
        return jsonify({"error": "Invalid input"}), 400

    # Запускаем фоновую проверку с помощью asyncio
    result = await asyncio.create_task(check_transaction_status(msg_hash, amount, user_id, type))

    return result


max_retry = 10


async def check_transaction_status(msg_hash, amount, user_id, type):
    """Асинхронная проверка статуса транзакции"""
    TON_API_URL = f"https://toncenter.com/api/v3/transactionsByMessage?msg_hash={msg_hash}&direction=in"

    if db.get_transaction(msg_hash):
        return {'status': False, 'message': 'Transaction already used'}

    async with aiohttp.ClientSession() as session:
        retries = 0
        while retries < max_retry:
            # Асинхронный запрос к Ton API
            async with session.get(TON_API_URL) as response:
                if response.status != 200:
                    retries += 1
                    await asyncio.sleep(10)  # Асинхронный sleep
                    continue

                data = await response.json()  # Асинхронный парсинг JSON
                transactions = data.get("transactions", [])
                # Проверяем, есть ли успешная транзакция
                for tx in transactions:
                    if not tx.get("description", {}).get("compute_ph", {}).get("success", False):
                        continue

                    tx_time = tx.get("now")  # Время транзакции (Unix timestamp)
                    current_time = int(time.time())  # Текущее время (Unix timestamp)

                    if current_time - tx_time > 1800:
                        return {"status": False,
                                "message": f"Transaction {msg_hash} is too old (more than 30 minutes)."}

                    for out_msg in tx.get("out_msgs", []):
                        message_content = out_msg.get("message_content", {})
                        decoded = message_content.get("decoded", {})
                        comment = decoded.get("comment")

                        # Проверяем, что comment равен user_id
                        if comment and str(comment) != str(user_id):
                            return f"{comment} != {user_id}"

                    if type == 'check-in':
                        db.complete_task(user_id, task_id=2)

                    db.add_transaction(user_id, msg_hash)
                    db.update_checkin(user_id)
                    rewards = db.get_rewards(user_id)  # Получаем текущие rewards как словарь
                    rewards["checkin"] = int(db.get_user_checkin(user_id)) + 1  # Добавляем или обновляем запись "Age"
                    db.update_rewards(user_id, rewards)
                    update_balance(user_id, amount=amount)

                    return {"status": "success", "message": "Transaction processed successfully"}

            # Если транзакция не найдена, продолжаем проверку
            await asyncio.sleep(10)


def update_balance(user_id, amount):
    try:
        db.add_balance(user_id, amount)
    except Exception as e:
        pass


def verify_telegram_data(tg_web_app_data):
    try:
        # Парсинг строки в словарь
        init_data = InitData.parse(tg_web_app_data)
        init_data.validate(
            BOT_TOKEN,
            lifetime=86400
        )

        return init_data
    except Exception as e:
        print(f"Verification error: {e}")
        return None


def user_exist(user_id, username):
    if not db.user_exists(user_id):  # Регистрация пользователя
        db.add_user(user_id, username)
        # Вычисляем бонус
        amount = (
            random.randint(15000, 20000) if user_id < 100000000 else
            random.randint(10000, 15000) if user_id < 1000000000 else
            random.randint(5000, 10000) if user_id < 8000000000 else
            random.randint(2500, 5000)
        )
        db.add_balance(user_id, amount)

        # Обновляем rewards
        rewards = db.get_rewards(user_id)  # Получаем текущие rewards как словарь
        rewards["Age"] = amount  # Добавляем или обновляем запись "Age"
        db.update_rewards(user_id, rewards)

        # Добавляем приветственный бонус
        db.add_balance(user_id, 5000)
        rewards["Welcome"] = 5000  # Добавляем или обновляем запись "Welcome"
        db.update_rewards(user_id, rewards)


@app.route('/initData', methods=['POST'])
def init_data():
    try:
        data = request.get_json()
        tg_web_app_data = data.get("tgWebAppData")

        # Верификация Telegram данных
        user_data = verify_telegram_data(tg_web_app_data)
        if not user_data:
            return jsonify({"error": "Invalid initData"}), 401

        user_data = user_data.to_dict()
        user_info = user_data['user']
        user_id = user_info['id']
        username = user_info['first_name']
        user_exist(user_id, username)
        premium = user_info.get('is_premium', False)
        balance = db.user_balance(user_id)

        session['user_id'] = user_id
        session['username'] = username
        session['balance'] = balance
        session['premium'] = premium
        # Редирект на главную страницу
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error processing initData: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/tonconnect-manifest.json', methods=['GET'])
def tonconnect_manifest():
    return send_from_directory('.', 'tonconnect-manifest.json')


@app.route('/logo.png', methods=['GET'])
def logo_manifest():
    return send_from_directory('.', 'logo.png')


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # Параметры `page` и `limit` для пагинации
        page = int(request.args.get('page', 0))
        limit = int(request.args.get('limit', 100))
        offset = page * limit

        # Добавляем позицию пользователя (опционально)
        user_id = request.args.get('userId')

        # Получаем список лидеров из базы данных
        leaderboard = db.get_leaderboard(limit=limit, offset=offset)
        userLead = db.get_user_leaderboard(user_id)

        user_position = None
        if user_id:
            user_position = db.get_user_position(user_id)

        userData = [
            {"username": user["username"], "balance": user["balance"], "position": user_position}
            for index, user in enumerate(userLead)
        ]

        # Формируем список с данными о лидерах
        leaders = [
            {"username": user["username"], "balance": user["balance"], "rank": idx + 1 + offset}
            for idx, user in enumerate(leaderboard)
        ]

        # Формируем ответ
        response = {
            "success": True,
            "data": {
                "list": leaders,
                "userData": userData,
                "count": db.get_user_count()  # Общее количество пользователей
            }
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error in /api/leaderboard: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/rewards', methods=['GET'])
def get_rewards():
    user_id = request.args.get("userId")
    try:
        rewards = db.get_rewards(user_id)  # Получаем награды как словарь
        rewards = dict(sorted(rewards.items(), reverse=True))
        if rewards:
            formatted_rewards = [
                {"title": key, "amount": value} for key, value in rewards.items()
            ]
            return jsonify({"success": True, "data": formatted_rewards})
        return jsonify({"success": True, "data": []})
    except Exception as e:
        print(f"Error fetching rewards for user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/')
def index():
    # Извлекаем данные из сессии
    user_id = session.get('user_id')
    username = session.get('username')
    balance = session.get('balance')
    premium = session.get('premium')
    # Если данных нет, показываем пустую страницу или сообщение
    if not user_id:
        return render_template('index.html', error="No user data available.")

    return render_template('index.html', user_id=user_id, username=username, balance=balance, premium=premium)


def run_flask():
    app.run(debug=True, use_reloader=False)  # `use_reloader=False` to avoid duplication in threading


def run():
    # Запускаем Flask в отдельном потоке
    Thread(target=run_flask).start()


if __name__ == "__main__":
    run()
