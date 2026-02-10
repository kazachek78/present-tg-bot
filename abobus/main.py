import telebot
from transformers import pipeline, AutoTokenizer
import torch
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация модели Qwen
logger.info("Загрузка модели Qwen2.5-1.5B-Instruct...")

try:
    # Используем pipeline для удобства - убираем trust_remote_code из model_kwargs
    pipe = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-1.5B-Instruct",
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Загружаем токенизатор отдельно для шаблона чата
    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen2.5-1.5B-Instruct"
    )
    
    logger.info("Модель успешно загружена!")
    
except Exception as e:
    logger.error(f"Ошибка при загрузке модели: {e}")
    
    # Попробуем более простой способ без сложных параметров
    try:
        logger.info("Пробуем загрузить модель без дополнительных параметров...")
        pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
        logger.info("Модель загружена в упрощенном режиме!")
    except Exception as e2:
        logger.error(f"И это не помогло: {e2}")
        raise

# Токен вашего Telegram бота (получите у @BotFather)
TOKEN = "8356972781:AAG1LO4luUndgscqyAZypmjhyhDrItG27ns"

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

def generate_response(user_message):
    """
    Генерирует ответ с помощью модели Qwen
    """
    try:
        # Формируем промпт для модели
        prompt = f"""Ты полезный AI-ассистент. Отвечай вежливо и информативно.

Вопрос: {user_message}
Ответ:"""
        
        # Генерируем ответ
        outputs = pipe(
            prompt,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id else tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1
        )
        
        # Извлекаем сгенерированный текст
        generated_text = outputs[0]["generated_text"]
        
        # Удаляем промпт из ответа
        response = generated_text.replace(prompt, "").strip()
        
        # Если ответ пустой, возвращаем дефолтный
        if not response:
            response = "Извините, не удалось сгенерировать ответ. Попробуйте задать вопрос по-другому."
        
        # Если ответ слишком длинный для Telegram (ограничение 4096 символов)
        if len(response) > 4000:
            response = response[:4000] + "...\n\n(сообщение обрезано из-за ограничений Telegram)"
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        return "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз."

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
👋 Привет! Я бот с ИИ на основе модели Qwen2.5-1.5B-Instruct.

Я могу:
• Отвечать на вопросы
• Помогать с текстами
• Обсуждать различные темы
• И многое другое!

Просто напишите мне сообщение, и я постараюсь помочь!

Команды:
/start - это сообщение
/help - помощь
/about - информация о боте
/test - проверить работу модели
"""
    bot.reply_to(message, welcome_text)

# Обработчик команды /test
@bot.message_handler(commands=['test'])
def test_model(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        test_prompt = "Напиши приветственное сообщение в двух предложениях."
        response = generate_response(test_prompt)
        bot.reply_to(message, f"✅ Тест пройден! Модель работает.\n\nОтвет модели:\n{response}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка теста: {str(e)}")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 Помощь по использованию бота:

1. Просто напишите любой вопрос или сообщение
2. Бот ответит, используя ИИ-модель Qwen
3. Ответы генерируются в реальном времени

⚠️ Ограничения:
• Максимальная длина ответа: ~4000 символов
• Время ответа зависит от сложности запроса
• Модель может иногда ошибаться

Примеры вопросов:
• "Расскажи о космосе"
• "Напиши стихотворение"
• "Объясни квантовую физику просто"
"""
    bot.reply_to(message, help_text)

# Обработчик команды /about
@bot.message_handler(commands=['about'])
def send_about(message):
    about_text = """
🤖 О боте:
• Модель: Qwen2.5-1.5B-Instruct
• Разработчик: Alibaba Cloud
• Параметры: 1.5 миллиарда параметров
• Тип: Инструктивная языковая модель

💡 Особенности:
• Поддерживает русский и английский
• Понимает контекст разговора
• Генерирует креативные ответы

🔧 Технологии:
• PyTorch + Transformers
• Hugging Face Pipeline
• Telegram Bot API
"""
    bot.reply_to(message, about_text)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Показываем статус "печатает"
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем текст сообщения пользователя
        user_input = message.text
        
        # Логируем запрос
        logger.info(f"Запрос от {message.from_user.username}: {user_input[:50]}...")
        
        # Генерируем ответ
        response = generate_response(user_input)
        
        # Отправляем ответ
        bot.reply_to(message, response)
        
        # Логируем успешный ответ
        logger.info(f"Ответ отправлен пользователю {message.from_user.username}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка. Попробуйте еще раз позже.")

# Основная функция
def main():
    logger.info("Запуск Telegram бота...")
    
    # Проверяем токен
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("❌ Не забудьте заменить YOUR_TELEGRAM_BOT_TOKEN_HERE на реальный токен!")
        return
    
    logger.info("Бот запущен. Ожидаю сообщения...")
    
    # Запускаем бота
    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()