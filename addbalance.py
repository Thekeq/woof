from db import DataBase

db = DataBase("data.db")

db.add_balance(427649607, 100000)
print("Баланс успешно изменен!")