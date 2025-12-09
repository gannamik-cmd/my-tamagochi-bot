import os
import random
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    print("Добавьте переменную BOT_TOKEN в настройки Render")
    exit(1)

# Импорты Telegram (новый стиль для версии 21.x)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    message = (
        f"🧬 Привет, {user.first_name}!\n\n"
        f"Я — Генетический бот 🧬\n"
        f"Расскажу о генетике в игровой форме!\n\n"
        f"📋 Команды:\n"
        f"/start - приветствие\n"
        f"/fact - случайный факт\n"
        f"/dna - создать ДНК-существо\n"
        f"/help - помощь\n\n"
        f"Напиши 'привет' или используй команды!"
    )
    await update.message.reply_text(message)

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /fact"""
    fact = random.choice(GENETIC_FACTS)
    await update.message.reply_text(f"📚 Факт о генетике:\n\n{fact}")

async def dna_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /dna"""
    # Генерируем случайное существо
    animals = ["🐱 Кот", "🐶 Собака", "🦊 Лиса", "🐰 Кролик", "🐻 Медведь", "🐯 Тигр"]
    colors = ["🔴 Красный", "🟢 Зеленый", "🔵 Синий", "🟡 Желтый", "🟣 Фиолетовый", "⚫ Черный"]
    powers = ["🦸 Супер-сила", "🧠 Телепатия", "👻 Невидимость", "✈️ Полет", "🏃 Быстрый бег", "👁️ Ночное зрение"]
    
    animal = random.choice(animals)
    color = random.choice(colors)
    power = random.choice(powers)
    creature_id = random.randint(1000, 9999)
    
    message = (
        f"🧪 Твое ДНК-существо создано!\n\n"
        f"🎭 Вид: {animal}\n"
        f"🎨 Цвет: {color}\n"
        f"⚡ Суперсила: {power}\n\n"
        f"🔢 ID: {creature_id}\n"
        f"🧬 Гены: {'доминантные' if random.random() > 0.5 else 'рецессивные'}\n\n"
        f"✨ Уникальное создание готово к приключениям!"
    )
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    message = (
        "🤖 Генетический бот - Помощь\n\n"
        "📚 Я умею:\n"
        "• /fact - рассказывать интересные факты о генетике\n"
        "• /dna - создавать уникальных ДНК-существ\n"
        "• Отвечать на простые вопросы\n\n"
        "💡 Просто напиши:\n"
        "- 'привет' для начала\n"
        "- 'ген' или 'днк' чтобы узнать больше\n"
        "- или используй команды выше!"
    )
    await update.message.reply_text(message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка обычных сообщений"""
    text = update.message.text.lower()
    
    if any(word in text for word in ['привет', 'здравствуй', 'хай', 'hello', 'hi']):
        await update.message.reply_text("👋 Привет! Давай изучать генетику вместе! Используй /fact")
    
    elif any(word in text for word in ['ген', 'генетика']):
        await update.message.reply_text("🧬 Гены - это инструкции для нашего организма! Хочешь создать свое существо? /dna")
    
    elif any(word in text for word in ['днк', 'dna']):
        await update.message.reply_text("🔬 ДНК хранит всю генетическую информацию! Узнать факт? /fact")
    
    elif any(word in text for word in ['спасибо', 'благодарю', 'thanks']):
        await update.message.reply_text("😊 Рад помочь! Продолжай изучать науку! 🧪")
    
    elif any(word in text for word in ['как дела', 'что нового']):
        await update.message.reply_text("Отлично! Готов создавать новых существ! /dna")
    
    else:
        await update.message.reply_text(
            "🤔 Не совсем понял...\n"
            "Попробуй:\n"
            "• /fact - узнать факт\n"
            "• /dna - создать существо\n"
            "• /help - помощь\n"
            "• или напиши 'привет'"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Что-то пошло не так. Попробуй еще раз!")
    except:
        pass

def main() -> None:
    """Основная функция запуска бота"""
    print("=" * 50)
    print("🚀 ЗАПУСК ГЕНЕТИЧЕСКОГО БОТА")
    print("=" * 50)
    
    # Создаем приложение
    try:
        application = Application.builder().token(TOKEN).build()
        print("✅ Приложение создано успешно")
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        return
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("fact", fact_command))
    application.add_handler(CommandHandler("dna", dna_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Обработчики зарегистрированы")
    print("🤖 Бот запущен и готов к работе!")
    print("📱 Ищите бота в Telegram и напишите /start")
    print("=" * 50)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
