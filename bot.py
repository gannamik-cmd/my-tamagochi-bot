import os
import logging
import sys
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# Получаем токен
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    logger.error("❌ ТОКЕН НЕ НАЙДЕН! Добавьте BOT_TOKEN в настройки Render")
    sys.exit(1)

# Факты о генетике
GENETIC_FACTS = [
    "🧬 ДНК человека на 99.9% одинакова у всех людей!",
    "🐒 Люди и бананы имеют 50% общих генов!",
    "👶 Ты получаешь гены от обоих родителей!",
    "🌈 Цвет глаз зависит от нескольких генов!",
    "🧪 Мутации бывают полезными, вредными и нейтральными!",
    "🔬 Генетика изучает наследственность и изменчивость!",
    "🧬 У каждого человека уникальная ДНК, кроме близнецов!",
    "🦠 Вирусы тоже имеют свою ДНК или РНК!"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    await update.message.reply_text(
        "👋 Привет, " + user.first_name + "!\n\n" +
        "Я — Генетический бот 🧬\n" +
        "Расскажу о генетике в игровой форме!\n\n" +
        "Команды:\n" +
        "/start - приветствие\n" +
        "/fact - случайный факт\n" +
        "/dna - создать ДНК-существо\n" +
        "/help - помощь\n\n" +
        "Просто напиши 'привет'!"
    )

async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /fact - случайный факт"""
    fact_text = random.choice(GENETIC_FACTS)
    await update.message.reply_text("📚 Факт о генетике:\n\n" + fact_text)

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
    
    message = (
        "🧪 Твое ДНК-существо создано!\n\n"
        "Внешность: " + head + "\n" +
        "Цвет: " + color + "\n" +
        "Суперсила: " + power + "\n\n" +
        "🎲 ID: " + str(creature_id) + "\n" +
        "🔬 Тип генов: " + gene_type + "\n\n" +
        "💡 Факт: " + ("Доминантные гены проявляются чаще!" if gene_type == "доминантный" 
                      else "Рецессивные гены могут скрываться!")
    )
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "🤖 Генетический бот - Помощь\n\n"
        "Я умею:\n"
        "• Рассказывать факты о генетике /fact\n"
        "• Создавать ДНК-существ /dna\n"
        "• Отвечать на вопросы\n\n"
        "Попробуй команду /dna !"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    text = update.message.text.lower()
    
    responses = {
        'привет': '👋 Привет! Узнаем о генетике? Используй /fact',
        'здравствуй': '👋 Здравствуй! Готов изучать генетику?',
        'ген': '🧬 Гены - это инструкции для организма! Попробуй /dna',
        'днк': '🔬 ДНК - молекула наследственности! Хочешь факт? /fact',
        'как дела': 'Отлично! Готов создавать ДНК-существ! /dna',
        'что умеешь': 'Я рассказываю о генетике! Используй /help',
        'спасибо': '😊 Всегда рад! Продолжай изучать науку!',

'хочу играть': '🎮 Отлично! Давай создадим существо! /dna',
        'факт': '📚 Используй команду /fact',
        'создать': '🧪 Используй /dna для создания существа',
    }
    
    for key, response in responses.items():
        if key in text:
            await update.message.reply_text(response)
            return
    
    # Если не нашли подходящий ответ
    await update.message.reply_text(
        "Не совсем понял... Попробуй команду:\n" +
        "/fact - интересный факт\n" +
        "/dna - создать существо\n" +
        "/help - помощь"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Ошибка: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуй еще раз!")
    except:
        pass

def main():
    """Запуск бота"""
    logger.info("🚀 Запуск генетического бота...")
    
    # Проверяем Python версию
    logger.info(f"Python version: {sys.version}")
    
    # Создаем приложение
    try:
        app = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.error(f"Ошибка создания приложения: {e}")
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
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if name == 'main':
    main()

