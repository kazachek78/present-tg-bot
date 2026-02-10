import telebot
from telebot import types
from transformers import pipeline
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация модели GPT
try:
    pipe = pipeline("text-generation", model="ai-forever/rugpt3medium_based_on_gpt2")
    logging.info("Модель GPT успешно загружена")
except Exception as e:
    logging.error(f"Ошибка загрузки модели: {e}")
    pipe = None

# Токен бота (замените на свой)

TOKEN = '8356972781:AAG1LO4luUndgscqyAZypmjhyhDrItG27ns'
bot = telebot.TeleBot(TOKEN)

# Хранилище данных пользователей (временное, для демо)
user_data = {}

# Клавиатура для выбора получателя
def get_recipient_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("Друг", callback_data="recipient_друг"),
        types.InlineKeyboardButton("Подруга", callback_data="recipient_подруга"),
        types.InlineKeyboardButton("Парень", callback_data="recipient_парень"),
        types.InlineKeyboardButton("Девушка", callback_data="recipient_девушка"),
        types.InlineKeyboardButton("Коллега", callback_data="recipient_коллега"),
        types.InlineKeyboardButton("Родители", callback_data="recipient_родители"),
        types.InlineKeyboardButton("Ребёнок", callback_data="recipient_ребенок"),
        types.InlineKeyboardButton("Другое", callback_data="recipient_другое"),
    ]
    keyboard.add(*buttons)
    return keyboard

# Клавиатура для выбора бюджета
def get_budget_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("До 1 000 ₽", callback_data="budget_1000"),
        types.InlineKeyboardButton("1 000 - 3 000 ₽", callback_data="budget_3000"),
        types.InlineKeyboardButton("3 000 - 5 000 ₽", callback_data="budget_5000"),
        types.InlineKeyboardButton("5 000 - 10 000 ₽", callback_data="budget_10000"),
        types.InlineKeyboardButton("10 000+ ₽", callback_data="budget_more"),
        types.InlineKeyboardButton("Не важно", callback_data="budget_any"),
    ]
    keyboard.add(*buttons)
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_data[message.chat.id] = {}
    
    welcome_text = (
        "🎁 *Привет! Я помогу выбрать подарок!*\n\n"
        "Для начала выберите, *кому* хотите сделать подарок:"
    )
    bot.send_message(message.chat.id, welcome_text, 
                     parse_mode='Markdown', reply_markup=get_recipient_keyboard())

# Обработчик инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        user_data[chat_id] = {}
    
    # Обработка выбора получателя
    if call.data.startswith('recipient_'):
        recipient = call.data.split('_')[1]
        user_data[chat_id]['recipient'] = recipient
        
        # Показываем выбор бюджета
        text = (
            f"🎯 Вы выбрали: *{recipient.capitalize()}*\n\n"
            "Теперь выберите *бюджет* на подарок:"
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=get_budget_keyboard()
        )
    
    # Обработка выбора бюджета
    elif call.data.startswith('budget_'):
        budget_map = {
            '1000': 'до 1 000 рублей',
            '3000': '1 000 - 3 000 рублей',
            '5000': '3 000 - 5 000 рублей',
            '10000': '5 000 - 10 000 рублей',
            'more': 'более 10 000 рублей',
            'any': 'не важно'
        }
        
        budget_key = call.data.split('_')[1]
        budget = budget_map.get(budget_key, 'не важно')
        user_data[chat_id]['budget'] = budget
        
        # Генерируем идеи подарков
        generate_gift_ideas(call.message, chat_id)

# Генерация идей подарков
def generate_gift_ideas(message, chat_id):
    if chat_id not in user_data or 'recipient' not in user_data[chat_id]:
        bot.send_message(chat_id, "Пожалуйста, начните с команды /start")
        return
    
    # Отправляем сообщение о генерации
    processing_msg = bot.send_message(
        chat_id, 
        "✨ Генерирую идеи подарков...\nЭто может занять 10-20 секунд."
    )
    
    recipient = user_data[chat_id]['recipient']
    budget = user_data[chat_id].get('budget', 'не важно')
    
    # Формируем промпт для модели
    prompt = f"""Предложи 5 конкретных идей подарков для {recipient} с бюджетом {budget}.

Требования:
1. Подарки должны быть практичными и уместными
2. Укажи примерную стоимость для каждого
3. Объясни, почему этот подарок подходит
4. Формат: пронумерованный список

Пример для друга с бюджетом 3000 рублей:
1. Беспроводные наушники (2500-3000 руб) - современно, удобно для спорта и путешествий
2. Книга по интересующей теме + кружка с принтом (1500-2000 руб) - персонализированный подарок

Идеи подарков для {recipient} (бюджет: {budget}):"""
    
    try:
        if pipe is None:
            raise Exception("Модель не загружена")
        
        # Генерация текста с помощью модели
        result = pipe(
            prompt,
            max_length=500,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=50256
        )
        
        generated_text = result[0]['generated_text']
        
        # Извлекаем только новые предложения (после промпта)
        if generated_text.startswith(prompt):
            ideas = generated_text[len(prompt):].strip()
        else:
            ideas = generated_text
        
        # Форматируем ответ
        response = (
            f"🎁 *Идеи подарков для {recipient.capitalize()}*\n"
            f"💰 *Бюджет:* {budget}\n\n"
            f"{ideas}\n\n"
            f"🔁 Чтобы начать заново, нажми /start\n"
            f"💡 *Совет:* Учитывайте интересы и увлечения человека!"
        )
        
        # Удаляем сообщение о генерации и отправляем результат
        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(chat_id, response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Ошибка генерации: {e}")
        
        # Запасные идеи (если модель не работает)
        backup_ideas = get_backup_ideas(recipient, budget)
        
        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(
            chat_id,
            backup_ideas,
            parse_mode='Markdown'
        )

# Запасные идеи (если модель недоступна)
def get_backup_ideas(recipient, budget):
    ideas_map = {
        'друг': [
            "🎧 Беспроводные наушники",
            "🔋 Power Bank большой емкости", 
            "🎮 Подарочная карта в Steam",
            "🧥 Стильный аксессуар (ремень, кошелек)",
            "📚 Книга по хобби"
        ],
        'подруга': [
            "💄 Набор косметики",
            "🌸 Цветы + шоколад премиум",
            "🕯 Ароматическая свеча с диффузором",
            "📖 Красивый ежедневник или блокнот",
            "🍵 Набор чая/кофе с красивой кружкой"
        ],
        'парень': [
            "⌚ Стильные часы",
            "🧴 Набор для ухода",
            "🎒 Качественный рюкзак",
            "⚽ Билеты на спортивное событие",
            "🔪 Мультитул или нож"
        ],
        'девушка': [
            "💍 Бижутерия (серьги, браслет)",
            "🧣 Шелковый шарф или палантин",
            "👜 Сумка-клатч",
            "🛁 Набор для ванны (бомбочки, соли)",
            "🎨 Набор для творчества"
        ]
    }
    
    ideas = ideas_map.get(recipient, [
        "📖 Книга по интересам",
        "🍫 Сладкий набор премиум-класса",
        "🎁 Подарочный сертификат",
        "🖼 Персонализированный подарок (фотоколлаж)",
        "🏆 Тематический сувенир"
    ])
    
    return (
        f"🎁 *Идеи подарков для {recipient.capitalize()}*\n"
        f"💰 *Бюджет:* {budget}\n\n"
        + "\n".join([f"• {idea}" for idea in ideas[:5]]) +
        f"\n\n*Примечание:* Модель временно недоступна. Эти идеи - общие рекомендации.\n"
        f"Чтобы попробовать снова, нажмите /start"
    )

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == '/start':
        start_message(message)
    else:
        bot.send_message(message.chat.id, 
                        "Используйте команду /start для начала работы с ботом!")

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logging.error(f"Ошибка в работе бота: {e}")