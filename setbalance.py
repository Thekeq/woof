from db import DataBase

db = DataBase("data.db")

db.set_balance(731928689, 44318)
print("Баланс успешно изменен!")