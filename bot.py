import os
import logging
import sys
import random

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импорты Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токен
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    logger.error("ТОКЕН НЕ НАЙДЕН! Добавьте BOT_TOKEN в настройки Render")
    sys.exit(1)

# Факты о генетике
GENETIC_FACTS = [
    "🧬 ДНК человека на 99.9% одинакова у всех людей!",
    "🐒 Люди и бананы имеют 50% общих генов!",
    "👶 Ты получаешь гены от обоих родителей!",
    "🌈 Цвет глаз зависит от нескольких генов!",
    "🧪 Мутации бывают полезными, вредными и нейтральными!",
    "🔬 Генетика изучает наследственность и изменчивость!",
    "👯 У каждого человека уникальная ДНК, кроме близнецов!",
    "🦠 Вирусы тоже имеют свою ДНК или РНК!"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    response = "🧬 Привет, " + user.first_name + "!\n\n"
    response += "Я — Генетический бот 🧬\n"
    response += "Расскажу о генетике в игровой форме!\n\n"
    response += "Команды:\n"
    response += "/start - приветствие\n"
    response += "/fact - случайный факт\n"
    response += "/dna - создать ДНК-существо\n"
    response += "/help - помощь\n\n"
    response += "Просто напиши 'привет'!"
    await update.message.reply_text(response)

async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /fact - случайный факт"""
    fact_text = random.choice(GENETIC_FACTS)
    response = "📚 Факт о генетике:\n\n" + fact_text
    await update.message.reply_text(response)

async def dna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /dna - создать существо"""
    # Части существ
    heads = ["🐱 кот", "🐶 собака", "🦊 лиса", "🐰 кролик", "🐻 медведь", "🐯 тигр"]
    colors = ["красный", "зеленый", "синий", "желтый", "фиолетовый", "радужный"]
    powers = ["супер-сила", "телепатия", "невидимость", "полет", "быстрый бег", "ночное зрение"]
    
    head = random.choice(heads)
    color = random.choice(colors)
    power = random.choice(powers)
    creature_id = random.randint(1000, 9999)
    gene_type = "доминантный" if random.random() > 0.5 else "рецессивный"
    
    message = "🧪 Твое ДНК-существо создано!\n\n"
    message += "Внешность: " + head + "\n"
    message += "Цвет: " + color + "\n"
    message += "Суперсила: " + power + "\n\n"
    message += "🎲 ID: " + str(creature_id) + "\n"
    message += "🔬 Тип генов: " + gene_type + "\n\n"
    
    if gene_type == "доминантный":
        message += "💡 Факт: Доминантные гены проявляются чаще!"
    else:
        message += "💡 Факт: Рецессивные гены могут скрываться!"
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    response = "🤖 Генетический бот - Помощь\n\n"
    response += "Я умею:\n"
    response += "• Рассказывать факты о генетике /fact\n"
    response += "• Создавать ДНК-существ /dna\n"
    response += "• Отвечать на вопросы\n\n"
    response += "Попробуй команду /dna !"
    await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    text = update.message.text.lower()
    
    if 'привет' in text or 'здравствуй' in text or 'хай' in text:
        await update.message.reply_text("👋 Привет! Узнаем о генетике? Используй /fact")
    elif 'ген' in text:
        await update.message.reply_text("🧬 Гены - это инструкции для организма! Попробуй /dna")
    elif 'днк' in text:
        await update.message.reply_text("🔬 ДНК - молекула наследственности! Хочешь факт? /fact")
    elif 'как дела' in text:
        await update.message.reply_text("Отлично! Готов создавать ДНК-существ! /dna")
    elif 'что умеешь' in text:
        await update.message.reply_text("Я рассказываю о генетике! Используй /help")
    elif 'спасибо' in text or 'благодарю' in text:
        await update.message.reply_text("😊 Всегда рад! Продолжай изучать науку!")
    elif 'хочу играть' in text or 'игра' in text:
        await update.message.reply_text("🎮 Отлично! Давай создадим существо! /dna")
    elif 'факт' in text:
        await update.message.reply_text("📚 Используй команду /fact")
    elif 'создать' in text or 'существо' in text:
        await update.message.reply_text("🧪 Используй /dna для создания существа")
    else:
        await update.message.reply_text(
            "Не совсем понял... Попробуй команду:\n" +
            "/fact - интересный факт\n" +
            "/dna - создать существо\n" +
            "/help - помощь"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error("Ошибка: %s", context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуй еще раз!")
    except:
        pass

def main():
    """Запуск бота"""
    logger.info("🚀 Запуск генетического бота...")
    
    # Проверяем Python версию
    logger.info("Python version: %s", sys.version)
    
    # Создаем приложение
    try:
        app = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.error("Ошибка создания приложения: %s", e)
        sys.exit(1)
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fact", fact))
    app.add_handler(CommandHandler("dna", dna))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запускаем
    logger.info("✅ Бот запущен! Ожидаю сообщений...")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error("Ошибка запуска бота: %s", e)
        sys.exit(1)

if __name__ == '__main__':
    main()
