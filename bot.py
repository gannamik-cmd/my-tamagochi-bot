
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# ========== ГЕНЕТИЧЕСКИЕ ДАННЫЕ ==========
GENES_DATABASE = {
    "eyes": {
        "blue": {"type": "рецессивный", "emoji": "👁️"},
        "brown": {"type": "доминантный", "emoji": "👁️"},
        "green": {"type": "рецессивный", "emoji": "👁️"}
    },
    "hair": {
        "dark": {"type": "доминантный", "emoji": "💇"},
        "blonde": {"type": "рецессивный", "emoji": "💇"},
        "red": {"type": "рецессивный", "emoji": "💇"}
    },
    "special_skill": {
        "super_hearing": {"type": "доминантный", "emoji": "👂"},
        "night_vision": {"type": "рецессивный", "emoji": "🌙"},
        "fast_run": {"type": "доминантный", "emoji": "🏃"}
    }
}

FACTS = [
    "🧬 ДНК человека на 99.9% идентична у всех людей!",
    "🦸 Мутации - это не всегда плохо. Без них не было бы эволюции!",
    "🐒 Люди и бананы имеют около 50% одинаковых генов!",
    "👶 Ты получаешь половину генов от мамы и половину от папы.",
    "🌈 Цвет глаз зависит от нескольких генов, а не от одного!"
]

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = (
        "👋 Привет, юный генетик!\n\n"
        "Я - ГеноМалыш, бот который расскажет тебе о генах и ДНК в игровой форме!\n\n"
        "📚 Доступные команды:\n"
        "/start - Начать общение\n"
        "/genebeast - Создать генетическое существо\n"
        "/fact - Интересный факт о генетике\n"
        "/mydna - Узнать свои виртуальные гены\n"
        "/sleep - Уложить бота спать (только для админов)\n"
        "/wakeup - Разбудить бота (только для админов)\n"
        "/status - Проверить состояние бота\n\n"
        "🎮 Просто напиши 'привет' или нажми на кнопки ниже!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧬 Создать существо", callback_data='create')],
        [InlineKeyboardButton("📚 Факт о генетике", callback_data='fact')],
        [InlineKeyboardButton("🧪 Мои гены", callback_data='mydna')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def genebeast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /genebeast - создать генетическое существо"""
    if not config.BOT_ACTIVE:
        await update.message.reply_text("😴 Бот спит. Используйте /wakeup чтобы разбудить.")
        return
    
    beast = create_genetic_beast()
    message = (
        f"🧬 Твое генетическое существо создано!\n\n"
        f"👁️ Глаза: {beast['eyes']} {GENES_DATABASE['eyes'][beast['eyes']]['emoji']}\n"
        f"💇 Волосы: {beast['hair']} {GENES_DATABASE['hair'][beast['hair']]['emoji']}\n"
        f"🎯 Суперсила: {beast['skill']} {GENES_DATABASE['special_skill'][beast['skill']]['emoji']}\n\n"
        f"🔬 Тип генов: {beast['gene_type']}\n"
        f"🎲 Уникальный ID: {beast['id']}\n\n"
        f"💡 Подсказка: {'доминантные' if beast['gene_type'] == 'доминантный' else 'рецессивные'} "
        f"гены проявляются чаще!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎲 Создать еще одного", callback_data='create')],
        [InlineKeyboardButton("📚 Объяснение", callback_data='explain')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):

Николь, [09.12.2025 19:30]
"""Команда /fact - случайный факт"""
    if not config.BOT_ACTIVE:
        await update.message.reply_text("😴 Бот спит. Используйте /wakeup чтобы разбудить.")
        return
    
    import random
    fact_text = random.choice(FACTS)
    await update.message.reply_text(f"📚 Факт о генетике:\n\n{fact_text}")

async def mydna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mydna - показать виртуальные гены пользователя"""
    if not config.BOT_ACTIVE:
        await update.message.reply_text("😴 Бот спит. Используйте /wakeup чтобы разбудить.")
        return
    
    # Создаем уникальный "генетический код" на основе ID пользователя
    user_id = update.effective_user.id
    dna_code = f"USER-{abs(user_id) % 10000:04d}"
    
    message = (
        f"🧬 Твой виртуальный генетический паспорт:\n\n"
        f"👤 ID ученого: {dna_code}\n"
        f"🔢 Уровень доступа: {'новичок' if user_id % 3 == 0 else 'стажер' if user_id % 3 == 1 else 'исследователь'}\n"
        f"🎯 Открытые гены: {len(GENES_DATABASE)} из 12\n"
        f"📊 Создано существ: {(user_id % 20) + 1}\n\n"
        f"💡 Продолжай изучать генетику, чтобы открывать новые возможности!"
    )
    await update.message.reply_text(message)

async def sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /sleep - уложить бота спать (только для админов)"""
    user_id = update.effective_user.id
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("⛔ Эта команда только для администраторов!")
        return
    
    config.BOT_ACTIVE = False
    await update.message.reply_text(
        "😴 Бот уходит спать...\n"
        "Буду игнорировать все сообщения кроме /wakeup\n"
        "Спокойной ночи! 💤"
    )

async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /wakeup - разбудить бота (только для админов)"""
    user_id = update.effective_user.id
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("⛔ Эта команда только для администраторов!")
        return
    
    config.BOT_ACTIVE = True
    await update.message.reply_text(
        "☀️ Бот проснулся и готов к работе!\n"
        "Приветствую, юные генетики! 🧬"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - проверить состояние бота"""
    status_text = "✅ Бот активен и готов к экспериментам!" if config.BOT_ACTIVE else "😴 Бот спит..."
    await update.message.reply_text(f"Статус бота:\n{status_text}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений (только если бот активен)"""
    if not config.BOT_ACTIVE:
        return  # Просто игнорируем сообщения
    
    text = update.message.text.lower()
    
    if text in ['привет', 'hello', 'hi', 'здравствуй']:
        await update.message.reply_text(
            "👋 Привет! Я ГеноМалыш. "
            "Используй /start чтобы увидеть все команды!"
        )
    elif 'ген' in text:
        await update.message.reply_text(
            "🧬 Гены - это инструкции для нашего тела! "
            "Хочешь создать свое существо? Используй /genebeast"
        )
    elif 'днк' in text or 'dna' in text:
        await update.message.reply_text(
            "🔬 ДНК - это молекула, которая хранит генетическую информацию. "
            "Хочешь факт? Используй /fact"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    if not config.BOT_ACTIVE:
        await update.callback_query.answer("Бот спит. Используйте /wakeup", show_alert=True)
        return
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'create':
        beast = create_genetic_beast()

Николь, [09.12.2025 19:30]
message = f"🎲 Новое существо создано!\nГлаза: {beast['eyes']}, Волосы: {beast['hair']}, Сила: {beast['skill']}"
        await query.edit_message_text(text=message)
    elif query.data == 'fact':
        import random
        await query.edit_message_text(text=f"📚 Факт:\n{random.choice(FACTS)}")
    elif query.data == 'mydna':
        dna_code = f"USER-{abs(query.from_user.id) % 10000:04d}"
        await query.edit_message_text(text=f"🧬 Твой генетический ID: {dna_code}")
    elif query.data == 'explain':
        await query.edit_message_text(
            text="🔍 Объяснение:\n\n"
            "• Доминантные гены 💪 проявляются чаще\n"
            "• Рецессивные гены 🕶️ могут 'прятаться'\n"
            "• У каждого существа уникальная комбинация!\n\n"
            "Это как смешивать цвета красок! 🎨"
        )

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def create_genetic_beast():
    """Создает случайное генетическое существо"""
    import random
    import hashlib
    
    # Выбираем случайные признаки
    eyes = random.choice(list(GENES_DATABASE['eyes'].keys()))
    hair = random.choice(list(GENES_DATABASE['hair'].keys()))
    skill = random.choice(list(GENES_DATABASE['special_skill'].keys()))
    
    # Определяем общий тип (преобладающий)
    genes_count = {
        'доминантный': 0,
        'рецессивный': 0
    }
    
    genes_count[GENES_DATABASE['eyes'][eyes]['type']] += 1
    genes_count[GENES_DATABASE['hair'][hair]['type']] += 1
    genes_count[GENES_DATABASE['special_skill'][skill]['type']] += 1
    
    gene_type = 'доминантный' if genes_count['доминантный'] >= 2 else 'рецессивный'
    
    # Создаем уникальный ID
    beast_string = f"{eyes}{hair}{skill}{random.randint(1, 1000)}"
    beast_id = hashlib.md5(beast_string.encode()).hexdigest()[:8].upper()
    
    return {
        'eyes': eyes,
        'hair': hair,
        'skill': skill,
        'gene_type': gene_type,
        'id': beast_id
    }

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка. Попробуйте еще раз или используйте /start"
        )

# ========== WEBHOOK НАСТРОЙКИ ДЛЯ RENDER ==========
async def set_webhook(application: Application):
    """Установка webhook для Render"""
    webhook_url = os.getenv("RENDER_WEBHOOK_URL")
    if webhook_url:
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")

def main():
    """Основная функция запуска бота"""
    # Проверка токена
    if not config.BOT_TOKEN:
        logger.error("Токен бота не найден! Проверьте файл .env")
        return
    
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genebeast", genebeast))
    application.add_handler(CommandHandler("fact", fact))
    application.add_handler(CommandHandler("mydna", mydna))
    application.add_handler(CommandHandler("sleep", sleep))
    application.add_handler(CommandHandler("wakeup", wakeup))
    application.add_handler(CommandHandler("status", status))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик обычных сообщений (с фильтром)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    port = int(os.environ.get('PORT', 8080))
    
    if 'RENDER' in os.environ:

Николь, [09.12.2025 19:30]
# На Render используем webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=config.BOT_TOKEN,
            webhook_url=f"https://genetics-bot.onrender.com/{config.BOT_TOKEN}"
        )
    else:
        # Локально используем polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == 'main':
    main()