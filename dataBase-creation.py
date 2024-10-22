import sqlite3

def create_table():
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
                        user_id INTEGER, item_id INTEGER,
                        count INTEGER, PRIMARY KEY (user_id, item_id))''')
    conn.commit()
    conn.close()

def create_orders_table():
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Добавляем уникальный идентификатор для заказа
                        user_id INTEGER, item_id INTEGER, count INTEGER, delivery_date DATE)''')
    conn.commit()
    conn.close()

create_orders_table()
create_table()