import telebot, sqlite3, json
from telebot import types
from datetime import datetime, timedelta

with open('config.json') as f:
    data = json.load(f)
    token = data['token']

bot = telebot.TeleBot(token)

catalog = [
    {"id": 1, "name": "Микроконтроллер CH340 NodeMcu V3\nWiFi, 30pin", "price": 188, "image_url": "https://i.imgur.com/HObAE2N.jpeg"},
    {"id": 2, "name": "Микроконтроллер ESP32\nWiFi + Bluetooth, 38pin", "price": 393, "image_url": "https://i.imgur.com/eUZSR0D.jpeg"},
    {"id": 3, "name": "Микроконтроллер Arduino PRO MICRO\n24pin", "price": 630, "image_url": "https://i.imgur.com/SsbgChF.jpeg"},
]

def add_to_cart_db(user_id, item_id):
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT count FROM cart WHERE user_id = ? AND item_id = ?', (user_id, item_id))
    result = cursor.fetchone()
    
    if result:
        new_count = result[0] + 1
        cursor.execute('UPDATE cart SET count = ? WHERE user_id = ? AND item_id = ?', (new_count, user_id, item_id))
    else:
        cursor.execute('INSERT INTO cart (user_id, item_id, count) VALUES (?, ?, ?)', (user_id, item_id, 1))
    
    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_id, count FROM cart WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_cart_items(user_id):
    items = get_cart(user_id)
    return [(item[0], item[1]) for item in items]

def add_order(user_id, item_id, count, delivery_date):
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders (user_id, item_id, count, delivery_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, item_id, count, delivery_date))
    
    conn.commit()
    conn.close()

def get_orders(user_id):
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_id, count, delivery_date FROM orders WHERE user_id = ?', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

@bot.message_handler(commands=['start'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("🛍 Каталог")
    button2 = types.KeyboardButton("🛒 Корзина")
    button3 = types.KeyboardButton("📦 Заказы")
    markup.add(button1, button2, button3)
    
    bot.send_message(message.chat.id, "Рады вас видеть!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🛍 Каталог")
def show_catalog(message):
    for item in catalog:
        bot.send_photo(message.chat.id, item['image_url'], caption=f"{item['name']} - {item['price']}₽", reply_markup=create_add_to_cart_button(item['id']))

def create_add_to_cart_button(item_id):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart:{item_id}")
    markup.add(button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_to_cart:"))
def add_to_cart(call):
    item_id = int(call.data.split(":")[1])
    user_id = call.from_user.id
    
    add_to_cart_db(user_id, item_id)
    
    item = next((item for item in catalog if item['id'] == item_id), None)
    if item:
        bot.answer_callback_query(call.id, f"{item['name']} добавлен в корзину!")
    else:
        bot.answer_callback_query(call.id, "Товар не найден.")

def create_buy_button(user_id):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Оплатить", callback_data=f"pay:{user_id}")
    button2 = types.InlineKeyboardButton("Очистить корзину", callback_data=f"clear_cart:{user_id}")
    markup.add(button, button2)
    return markup

@bot.message_handler(func=lambda message: message.text == "🛒 Корзина")
def show_cart(message):
    user_id = message.from_user.id
    cart_items = get_cart_items(user_id)

    if cart_items:
        items = []
        total = 0

        for item_id, count in cart_items:
            item = next((item for item in catalog if item['id'] == item_id), None)
            if item:
                items.append(f"Товар: {item['name']} - {count} шт. по {item['price']}₽")
                total += item['price'] * count

        items_message = "\n".join(items)
        bot.send_message(message.chat.id, f"Ваша корзина:\n{items_message}\n\nИтого: {total}₽", reply_markup=create_buy_button(user_id))
    else:
        bot.send_message(message.chat.id, "Ваша корзина пуста.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay:"))
def handle_payment(call):
    user_id = call.data.split(":")[1]
    cart_items = get_cart_items(user_id)
    
    if cart_items:
        delivery_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        for item_id, count in cart_items:
            add_order(user_id, item_id, count, delivery_date)
        
        bot.answer_callback_query(call.id, "Оплата прошла успешно!")
        
        conn = sqlite3.connect('sqliteDB.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(call.message.chat.id, f"Ваш заказ оформлен и будет доставлен {delivery_date}!")
    else:
        bot.answer_callback_query(call.id, "Ваша корзина пуста.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_cart:"))
def clear_cart(call):
    user_id = call.data.split(":")[1]
    conn = sqlite3.connect('sqliteDB.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, "Корзина очищена.")
    bot.send_message(call.message.chat.id, "Ваша корзина была очищена.")

@bot.message_handler(func=lambda message: message.text == "📦 Заказы")
def show_orders(message):
    user_id = message.from_user.id
    orders = get_orders(user_id)

    if orders:
        order_messages = []
        for item_id, count, delivery_date in orders:
            item = next((item for item in catalog if item['id'] == item_id), None)
            if item:
                order_messages.append(f"Товар: {item['name']} - {count} шт. | Дата доставки: {delivery_date}")
        
        orders_message = "\n".join(order_messages)
        bot.send_message(message.chat.id, f"Ваши заказы:\n{orders_message}")
    else:
        bot.send_message(message.chat.id, "У вас нет заказов.")


bot.infinity_polling()