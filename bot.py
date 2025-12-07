
import logging
import random
import json
import datetime
import os
from enum import Enum
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)

# Загружаем токен из .env файла
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: Токен бота не найден!")
    print("Создайте файл .env в папке с ботом и добавьте:")
    print("TELEGRAM_BOT_TOKEN=ваш_токен_здесь")
    exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ГЛОБАЛЬНЫЙ ФЛАГ СОСТОЯНИЯ СНА БОТА
BOT_IS_SLEEPING = False

# Состояния персонажа
class Gender(Enum):
    BOY = "мальчик"
    GIRL = "девочка"

class Mood(Enum):
    HAPPY = "😊 Счастливый"
    NEUTRAL = "😐 Нейтральный"
    SAD = "😢 Грустный"
    ANGRY = "😠 Злой"
    SICK = "🤒 Болен"
    EXCITED = "🤩 В восторге"
    TIRED = "😪 Уставший"

class AgeGroup(Enum):
    BABY = "младенец (0-2)"
    CHILD = "ребёнок (3-6)"
    SCHOOL1 = "младший школьник (7-10)"
    SCHOOL2 = "подросток (11-13)"
    TEEN = "подросток (14-16)"
    ADULT = "взрослый (17+)"

# Генератор текста для событий
class EventGenerator:
    @staticmethod
    def get_morning_event(name: str, gender: Gender, discipline: int) -> str:
        events = [
            f"{name} {'' if gender == Gender.BOY else 'само'}проснулся{'ась' if gender == Gender.GIRL else ''} с первыми лучами солнца! ☀️",
            f"{name} не хотел{'а' if gender == Gender.GIRL else ''} вставать, но будильник сделал свое дело. ⏰",
            f"{name} встретил{'а' if gender == Gender.GIRL else ''} утро с улыбкой и бодростью! 😄"
        ]
        if discipline > 70:
            return random.choice([
                f"{name} сам{'о' if gender == Gender.GIRL else ''} проснулся{'ась' if gender == Gender.GIRL else ''} по расписанию, без будильника! ⭐",
                f"{name} начал{'а' if gender == Gender.GIRL else ''} день с утренней медитации. 🧘"
            ])
        return random.choice(events)
    
    @staticmethod
    def get_school_event(name: str, gender: Gender, lessons: int) -> str:
        if lessons == 0:
            return random.choice([
                f"{name} решил{'а' if gender == Gender.GIRL else ''} прогулять школу и отправился{'ась' if gender == Gender.GIRL else ''} в парк. 🌳",
                f"{name} притворился{'ась' if gender == Gender.GIRL else ''} больным{'ой' if gender == Gender.GIRL else 'ым'}, чтобы не идти в школу. 🤒",
                f"{name} забыл{'а' if gender == Gender.GIRL else ''} про школу и проспал{'а' if gender == Gender.GIRL else ''} все уроки. 😴"
            ])
        
        subjects = ["математике", "литературе", "истории", "биологии", "физике", "химии"]
        event = random.choice([
            f"получил{'а' if gender == Gender.GIRL else ''} пятерку по {random.choice(subjects)}! 🏆",
            f"участвовал{'а' if gender == Gender.GIRL else ''} в олимпиаде по {random.choice(subjects)}. 📝",
            f"помог{'ла' if gender == Gender.GIRL else ''} однокласснику с домашним заданием. 👥",
            f"поссорился{'ась' if gender == Gender.GIRL else ''} с другом на перемене. 😠",
            f"съел{'а' if gender == Gender.GIRL else ''} вкусный пирог в столовой. 🥧"
        ])
        return f"В школе {name} {event}"
    
    @staticmethod
    def get_evening_event(name: str, gender: Gender) -> str:
        activities = [
            ("играл{'а' if gender == Gender.GIRL else ''} в компьютерные игры", "🎮"),
            ("рисовал{'а' if gender == Gender.GIRL else ''} картину", "🎨"),
            ("читал{'а' if gender == Gender.GIRL else ''} интересную книгу", "📚"),
            ("готовил{'а' if gender == Gender.GIRL else ''} печенье", "🍪"),
            ("смотрел{'а' if gender == Gender.GIRL else ''} фильм", "🎬"),
            ("занимался{'ась' if gender == Gender.GIRL else ''} спортом", "💪"),
            ("ходил{'а' if gender == Gender.GIRL else ''} в гости к другу", "👥"),
            ("посетил{'а' if gender == Gender.GIRL else ''} выставку", "🖼️"),
            ("был{'а' if gender == Gender.GIRL else ''} в театре", "🎭"),
            ("гулял{'а' if gender == Gender.GIRL else ''} в парке", "🌳")
        ]
        activity, emoji = random.choice(activities)
        return f"Вечером {name} {activity}. {emoji}"
    
    @staticmethod
    def get_life_event(name: str, gender: Gender) -> tuple:
        """Возвращает (текст_события, эффект_характеристики, значение, эффект_очков, значение)"""
        events = [
            (
                f"{name} нашёл{'ла' if gender == Gender.GIRL else ''} на улице кошелек и сдал{'а' if gender == Gender.GIRL else ''} его в полицию",
                "reputation", 15, "money", 10
            ),
            (
                f"{name} помог{'ла' if gender == Gender.GIRL else ''} пожилому человеку донести сумки",
                "social", 10, "reputation", 10
            ),
            (
                f"{name} выиграл{'а' if gender == Gender.GIRL else ''} школьную олимпиаду",
                "intelligence", 10, "career", 20
            ),
            (
                f"{name} получил{'а' if gender == Gender.GIRL else ''} стипендию за хорошую учебу",
                "money", 50, "discipline", 10
            ),
            (
                f"{name} подрался{'ась' if gender == Gender.GIRL else ''} с одноклассником",
                "health", -15, "criminal", 10
            ),
            (
                f"{name} прогулял{'а' if gender == Gender.GIRL else ''} все уроки",
                "discipline", -10, "criminal", 15
            ),
            (
                f"{name} организовал{'а' if gender == Gender.GIRL else ''} вечеринку для друзей",
                "social", 15, "happiness", 20
            ),
            (
                f"{name} начал{'а' if gender == Gender.GIRL else ''} вести блог о своих увлечениях",
                "creativity", 10, "social", 10
            )
        ]
        return random.choice(events)

# Класс Тамагочи
class Tamagochi:
    def __init__(self, name: str, gender: Gender):
        self.name = name
        self.gender = gender
        self.age_days = 0
        self.age_group = AgeGroup.BABY
        
        # Основные характеристики
        self.health = 100
        self.hunger = 0
        self.hygiene = 100
        self.energy = 100
        self.happiness = 100
        self.intelligence = 10
        self.money = 50
        self.discipline = 50
        self.social = 50
        self.mood = Mood.HAPPY
        self.reputation = 50
        self.creativity = 50
        
        # Состояния
        self.is_sleeping = True
        self.is_sick = False
        self.is_at_school = False
        self.location = "дом"
        self.current_activity = None
        
        # Достижения и история
        self.skills = {
            "учёба": 0,
            "спорт": 0,
            "творчество": 0,
            "социальные": 0
        }
        self.daily_stats = {
            "lessons_attended": 0,
            "meals_eaten": 0,
            "studied": 0,
            "entertainment": 0
        }
        self.career_points = 0
        self.criminal_points = 0
        self.inventory = []
        self.friends = []
        self.relationships = {}
        
        # Время последних действий
        self.last_meal = None
        self.last_bath = None
        self.last_study = None
        
        # Генератор событий
        self.event_gen = EventGenerator()
    
    def update_age(self):
        # Ускоренное взросление: 1 игровой день = 100 дней жизни
        self.age_days += 100
        
        if self.age_days < 730:
            self.age_group = AgeGroup.BABY
        elif self.age_days < 2190:
            self.age_group = AgeGroup.CHILD
        elif self.age_days < 3650:
            self.age_group = AgeGroup.SCHOOL1
        elif self.age_days < 4745:
            self.age_group = AgeGroup.SCHOOL2
        elif self.age_days < 5840:
            self.age_group = AgeGroup.TEEN
        else:
            self.age_group = AgeGroup.ADULT
    
    def update_mood(self):
        if self.is_sick:
            self.mood = Mood.SICK
            return
            
        mood_score = (
            self.happiness * 0.3 +
            self.health * 0.2 +
            (100 - self.hunger) * 0.2 +
            self.energy * 0.15 +
            (100 - self.hygiene) * 0.15
        )
        
        if self.energy < 30:
            self.mood = Mood.TIRED
        elif mood_score > 85:
            self.mood = Mood.HAPPY
        elif mood_score > 70:
            self.mood = Mood.EXCITED
        elif mood_score > 50:
            self.mood = Mood.NEUTRAL
        elif mood_score > 30:
            self.mood = Mood.SAD
        else:
            self.mood = Mood.ANGRY
    
    def natural_changes(self):
        # Естественные изменения характеристик
        self.hunger += random.randint(1, 3)
        self.hygiene -= random.randint(1, 5)
        self.energy -= random.randint(1, 4)
        
        if self.hunger > 80:
            self.health -= 2
            self.happiness -= 3
        elif self.hunger > 50:
            self.health -= 1
            self.happiness -= 1
            
        if self.hygiene < 30:
            self.health -= 2
            self.happiness -= 2
            
        if self.energy < 30:
            self.health -= 1
            
        # Шанс заболеть
        if random.random() < 0.1 and self.hygiene < 40:
            self.is_sick = True
            self.health -= 10
            
        # Шанс улучшения настроения от хороших условий
        if self.hunger < 20 and self.hygiene > 80 and self.energy > 70:
            self.happiness += random.randint(1, 3)
            
        # Ограничения значений
        self.health = max(0, min(100, self.health))
        self.hunger = max(0, min(100, self.hunger))
        self.hygiene = max(0, min(100, self.hygiene))
        self.energy = max(0, min(100, self.energy))
        self.happiness = max(0, min(100, self.happiness))
        
        self.update_mood()
    
    def to_dict(self):
        return {
            "name": self.name,
            "gender": self.gender.value,
            "age_days": self.age_days,
            "age_group": self.age_group.value,
            "health": self.health,
            "hunger": self.hunger,
            "hygiene": self.hygiene,
            "energy": self.energy,
            "happiness": self.happiness,
            "intelligence": self.intelligence,
            "money": self.money,
            "discipline": self.discipline,
            "social": self.social,
            "creativity": self.creativity,
            "mood": self.mood.value,
            "reputation": self.reputation,
            "is_sleeping": self.is_sleeping,
            "is_sick": self.is_sick,
            "skills": self.skills,
            "career_points": self.career_points,
            "criminal_points": self.criminal_points,
            "inventory": self.inventory,
            "friends": self.friends
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        gender = Gender(data["gender"])
        tamagochi = cls(data["name"], gender)
        
        tamagochi.age_days = data["age_days"]
        tamagochi.age_group = AgeGroup(data["age_group"])
        tamagochi.health = data["health"]
        tamagochi.hunger = data["hunger"]
        tamagochi.hygiene = data["hygiene"]
        tamagochi.energy = data["energy"]
        tamagochi.happiness = data["happiness"]
        tamagochi.intelligence = data["intelligence"]
        tamagochi.money = data["money"]
        tamagochi.discipline = data["discipline"]
        tamagochi.social = data["social"]
        tamagochi.creativity = data.get("creativity", 50)
        
        for mood in Mood:
            if mood.value == data["mood"]:
                tamagochi.mood = mood
                break
                
        tamagochi.reputation = data["reputation"]
        tamagochi.is_sleeping = data.get("is_sleeping", False)
        tamagochi.is_sick = data.get("is_sick", False)
        tamagochi.skills = data["skills"]
        tamagochi.career_points = data["career_points"]
        tamagochi.criminal_points = data["criminal_points"]
        tamagochi.inventory = data["inventory"]
        tamagochi.friends = data["friends"]
        
        return tamagochi

# Глобальное хранилище данных
user_tamagochi = {}
user_save_file = "tamagochi_data.json"

def load_data():
    global user_tamagochi
    try:
        with open(user_save_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for user_id, tam_data in data.items():
                user_tamagochi[int(user_id)] = Tamagochi.from_dict(tam_data)
        logger.info("Данные загружены")
    except FileNotFoundError:
        logger.info("Файл данных не найден, создаем новый")

def save_data():
    data = {}
    for user_id, tamagochi in user_tamagochi.items():
        data[str(user_id)] = tamagochi.to_dict()
    
    with open(user_save_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Данные сохранены")

# ====== ФУНКЦИЯ ДЛЯ ПРОВЕРКИ СНА БОТА ======
async def check_bot_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE, command_to_check: str = None) -> bool:
    """
    Проверяет, спит ли бот. Если спит и команда не /wakeup - игнорирует сообщение.
    Возвращает True если нужно обрабатывать сообщение, False если игнорировать.
    """
    global BOT_IS_SLEEPING
    
    if BOT_IS_SLEEPING:
        # Если бот спит, проверяем, это команда /wakeup?
        if update.message and update.message.text:
            text = update.message.text.lower()
            # Разрешаем только команду /wakeup
            if text.startswith('/wakeup'):
                return True  # Обрабатываем /wakeup
            # Все остальные сообщения игнорируем
            return False  # Игнорируем
        elif update.callback_query:
            # Все callback-запросы игнорируем
            return False
    
    # Если бот не спит - обрабатываем всё
    return True

# ====== КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ СНОМ БОТА ======
async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Укладывает бота спать"""
    global BOT_IS_SLEEPING
    
    # Проверяем, не спит ли уже бот
    if not await check_bot_sleep(update, context, "/sleep"):
        return
    
    BOT_IS_SLEEPING = True
    logger.info(f"Бот уснул по команде от пользователя {update.effective_user.id}")
    
    await update.message.reply_text(
        "💤 Бот засыпает... Zzz\n\n"
        "Теперь бот не будет реагировать на сообщения.\n"
        "Чтобы разбудить бота, используйте команду: /wakeup"
    )

async def wakeup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Будит бота"""
    global BOT_IS_SLEEPING
    
    BOT_IS_SLEEPING = False
    logger.info(f"Бот проснулся по команде от пользователя {update.effective_user.id}")
    
    await update.message.reply_text(
        "☀️ Бот проснулся и готов к работе!\n\n"
        "Теперь бот снова отвечает на команды.\n"
        "Чтобы уложить спать: /sleep"
    )

async def status_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает состояние бота (спит или нет)"""
    global BOT_IS_SLEEPING
    
    # Проверяем, не спит ли бот (для этой команды делаем исключение)
    if not await check_bot_sleep(update, context, "/status_bot"):
        return
    
    if BOT_IS_SLEEPING:
        status_text = "💤 Бот спит\nИгнорирует все сообщения кроме /wakeup"
    else:
        status_text = "☀️ Бот бодрствует\nОтвечает на все команды"
    
    await update.message.reply_text(
        f"🤖 СОСТОЯНИЕ БОТА:\n\n{status_text}\n\n"
        f"Команды управления:\n"
        f"/sleep - уложить бота спать\n"
        f"/wakeup - разбудить бота\n"
        f"/status_bot - проверить состояние"
    )

# ====== ОБНОВЛЁННЫЕ КОМАНДЫ БОТА С ПРОВЕРКОЙ СНА ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/start"):
        return
    
    user_id = update.effective_user.id
    
    if user_id in user_tamagochi:
        await show_status(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("👧 Девочка", callback_data="gender_girl")],
        [InlineKeyboardButton("👦 Мальчик", callback_data="gender_boy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в игру 'Виртуальный ребенок'!\n\n"
        "Вы становитесь родителем ребенка, который будет расти и развиваться.\n"
        "Ваши решения повлияют на его будущее!\n\n"
        "К 13 годам ребенок может:\n"
        "✅ Разбогатеть и стать успешным\n"
        "❌ Попасть в тюрьму из-за плохого воспитания\n\n"
        "Выберите пол вашего ребенка:",
        reply_markup=reply_markup
    )

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "set_gender"):
        return
    
    query = update.callback_query
    await query.answer()
    
    gender_type = query.data.split("_")[1]
    context.user_data['gender'] = Gender.GIRL if gender_type == "girl" else Gender.BOY
    
    await query.edit_message_text(
        f"Отлично! Вы выбрали {context.user_data['gender'].value}!\n\n"
        f"Придумайте имя для вашего ребенка:\n"
        f"(Напишите в чат)"
    )

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "set_name"):
        return
    
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    if not name or len(name) > 20:
        await update.message.reply_text("Имя должно быть от 1 до 20 символов. Попробуйте еще раз:")
        return
    
    gender = context.user_data.get('gender', Gender.BOY)
    tamagochi = Tamagochi(name, gender)
    user_tamagochi[user_id] = tamagochi
    
    save_data()
    
    await update.message.reply_text(
        f"🎉 Поздравляем! У вас родился{'ся' if gender == Gender.BOY else 'ась'} {name}!\n\n"
        f"Теперь вы можете ухаживать за своим ребенком.\n\n"
        f"Новые команды управления ботом:\n"
        f"/sleep - уложить бота спать\n"
        f"/wakeup - разбудить бота\n"
        f"/status_bot - состояние бота\n\n"
        f"Основные команды игры:\n"
        f"/status - состояние ребенка\n"
        f"/daily - ежедневная рутина\n"
        f"/care - уход за ребенком\n"
        f"/event - случайное событие\n"
        f"/destiny - проверить судьбу\n"
        f"/help - все команды"
    )
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "show_main_menu"):
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status")],
        [InlineKeyboardButton("🌅 День ребенка", callback_data="action_daily")],
        [InlineKeyboardButton("👶 Уход", callback_data="action_care")],
        [InlineKeyboardButton("🎭 Событие", callback_data="action_event")],
        [InlineKeyboardButton("🔮 Судьба", callback_data="action_destiny")],
        [InlineKeyboardButton("🔄 Сбросить день", callback_data="action_reset_day")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Главное меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=reply_markup
        )

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/status"):
        return
    
    user_id = update.effective_user.id
    
    if user_id not in user_tamagochi:
        await update.message.reply_text("У вас еще нет ребенка! Используйте /start для создания.")
        return
    
    tamagochi = user_tamagochi[user_id]
    
    age_years = tamagochi.age_days // 365
    age_months = (tamagochi.age_days % 365) // 30
    
    # Индикаторы прогресса
    def progress_bar(value, max_value=100):
        filled = int(value / max_value * 10)
        return "█" * filled + "░" * (10 - filled)
    
    # Показываем состояние бота в статусе
    global BOT_IS_SLEEPING
    bot_status = "💤 Спит" if BOT_IS_SLEEPING else "☀️ Бодрствует"
    
    status_text = f"""
👤 *{tamagochi.name}* ({tamagochi.gender.value})
🤖 *Состояние бота:* {bot_status}

🎂 *Возраст:* {age_years} лет, {age_months} месяцев ({tamagochi.age_days} дней)
📊 *Группа:* {tamagochi.age_group.value}
🎭 *Настроение:* {tamagochi.mood.value}
📍 *Локация:* {tamagochi.location}
{'💤 *Спит*' if tamagochi.is_sleeping else '👁️ *Бодрствует*'}
{'🤒 *Болен*' if tamagochi.is_sick else '✅ *Здоров*'}

📈 *ОСНОВНЫЕ ПОКАЗАТЕЛИ:*
❤️ Здоровье: {progress_bar(tamagochi.health)} {tamagochi.health}/100
🍎 Голод: {progress_bar(100 - tamagochi.hunger)} {100 - tamagochi.hunger}/100
🚿 Чистота: {progress_bar(tamagochi.hygiene)} {tamagochi.hygiene}/100
⚡ Энергия: {progress_bar(tamagochi.energy)} {tamagochi.energy}/100
😊 Счастье: {progress_bar(tamagochi.happiness)} {tamagochi.happiness}/100

🧠 *РАЗВИТИЕ:*
💰 Деньги: {tamagochi.money} руб.
📚 Интеллект: {tamagochi.intelligence}
🎨 Творчество: {tamagochi.creativity}
👥 Общительность: {tamagochi.social}
⚖️ Дисциплина: {tamagochi.discipline}
⭐ Репутация: {tamagochi.reputation}

🏆 *НАВЫКИ:*
• 📚 Учёба: {tamagochi.skills['учёба']}
• 💪 Спорт: {tamagochi.skills['спорт']}
• 🎨 Творчество: {tamagochi.skills['творчество']}
• 👥 Социальные: {tamagochi.skills['социальные']}

🎯 *ЖИЗНЕННЫЙ ПУТЬ:*
• 🚀 Карьерные очки: {tamagochi.career_points}
• ⚠️ Криминальные очки: {tamagochi.criminal_points}

📊 *СЕГОДНЯ:*
• 🏫 Уроков: {tamagochi.daily_stats['lessons_attended']}
• 🍽️ Приемов пищи: {tamagochi.daily_stats['meals_eaten']}
• 📖 Учебы: {tamagochi.daily_stats['studied']}
• 🎮 Развлечений: {tamagochi.daily_stats['entertainment']}
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="action_status"),
         InlineKeyboardButton("🌅 День ребенка", callback_data="action_daily")],
        [InlineKeyboardButton("👶 Уход", callback_data="action_care"),
         InlineKeyboardButton("🎭 Событие", callback_data="action_event")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            status_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            status_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def daily_routine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/daily"):
        return
    
    user_id = update.effective_user.id
    
    if user_id not in user_tamagochi:
        await update.message.reply_text("У вас еще нет ребенка!")
        return
    
    tamagochi = user_tamagochi[user_id]
    events = []
    
    # Сброс дневной статистики
    tamagochi.daily_stats = {
        "lessons_attended": 0,
        "meals_eaten": 0,
        "studied": 0,
        "entertainment": 0
    }
    
    # Обновление возраста и естественные изменения
    tamagochi.update_age()
    tamagochi.natural_changes()
    
    # 1. ПРОБУЖДЕНИЕ
    if tamagochi.is_sleeping:
        wake_event = tamagochi.event_gen.get_morning_event(
            tamagochi.name, tamagochi.gender, tamagochi.discipline
        )
        events.append(f"🌅 *Утро:* {wake_event}")
        tamagochi.is_sleeping = False
        tamagochi.energy = min(100, tamagochi.energy + 40)
    
    # 2. УМЫВАНИЕ
    if random.random() < 0.8:
        tamagochi.hygiene = min(100, tamagochi.hygiene + 30)
        events.append(f"🚿 *Умывание:* {tamagochi.name} умылся{'ась' if tamagochi.gender == Gender.GIRL else ''}")
    
    # 3. ЗАВТРАК
    if tamagochi.hunger > 20:
        tamagochi.hunger = max(0, tamagochi.hunger - 40)
        tamagochi.health = min(100, tamagochi.health + 5)
        tamagochi.daily_stats["meals_eaten"] += 1
        events.append(f"🍳 *Завтрак:* {tamagochi.name} позавтракал{'а' if tamagochi.gender == Gender.GIRL else ''}")
    
    # 4. ЗАРЯДКА (зависит от дисциплины)
    if tamagochi.discipline > 60 and random.random() < 0.7:
        tamagochi.health = min(100, tamagochi.health + 10)
        tamagochi.energy = min(100, tamagochi.energy + 5)
        tamagochi.skills["спорт"] += 1
        events.append(f"💪 *Зарядка:* {tamagochi.name} сделал{'а' if tamagochi.gender == Gender.GIRL else ''} утреннюю зарядку")
    
    # 5. ЗАПРАВКА КРОВАТИ
    if tamagochi.discipline > 50:
        tamagochi.discipline += 2
        events.append(f"🛏️ *Порядок:* {tamagochi.name} заправил{'а' if tamagochi.gender == Gender.GIRL else ''} кровать")
    
    # 6. ШКОЛА (только для школьного возраста)
    if tamagochi.age_group in [AgeGroup.SCHOOL1, AgeGroup.SCHOOL2, AgeGroup.TEEN]:
        # Решение идти в школу
        if tamagochi.discipline > 40 or random.random() < 0.6:
            lessons = random.randint(3, 6) if tamagochi.discipline > 60 else random.randint(1, 4)
            tamagochi.is_at_school = True
            
            school_event = tamagochi.event_gen.get_school_event(
                tamagochi.name, tamagochi.gender, lessons
            )
            events.append(f"🏫 *Школа:* {school_event}")
            
            if lessons > 0:
                tamagochi.intelligence += lessons
                tamagochi.skills["учёба"] += lessons
                tamagochi.discipline += lessons * 2
                tamagochi.career_points += lessons * 3
                tamagochi.daily_stats["lessons_attended"] = lessons
                tamagochi.energy = max(0, tamagochi.energy - lessons * 5)
            else:
                tamagochi.discipline -= 10
                tamagochi.criminal_points += 5
                tamagochi.happiness += 20
        else:
            events.append(f"🏠 *Дом:* {tamagochi.name} остался{'ась' if tamagochi.gender == Gender.GIRL else ''} дома (каникулы/выходной)")
    
    # 7. ОБЕД
    tamagochi.hunger = max(0, tamagochi.hunger - 30)
    tamagochi.health = min(100, tamagochi.health + 3)
    tamagochi.daily_stats["meals_eaten"] += 1
    events.append(f"🥗 *Обед:* {tamagochi.name} пообедал{'а' if tamagochi.gender == Gender.GIRL else ''}")
    
    # 8. ДНЕВНЫЕ АКТИВНОСТИ (после школы)
    evening_event = tamagochi.event_gen.get_evening_event(tamagochi.name, tamagochi.gender)
    events.append(f"🌇 *День:* {evening_event}")
    
    # Эффекты от вечернего занятия
    tamagochi.happiness = min(100, tamagochi.happiness + 15)
    tamagochi.energy = max(0, tamagochi.energy - 10)
    tamagochi.social = min(100, tamagochi.social + 5)
    tamagochi.daily_stats["entertainment"] += 1
    
    # 9. УЖИН
    tamagochi.hunger = max(0, tamagochi.hunger - 25)
    tamagochi.daily_stats["meals_eaten"] += 1
    events.append(f"🍲 *Ужин:* {tamagochi.name} поужинал{'а' if tamagochi.gender == Gender.GIRL else ''}")
    
    # 10. ВЕЧЕРНИЕ ПРОЦЕДУРЫ
    bath_type = random.choice(["ванне", "душе"])
    tamagochi.hygiene = min(100, tamagochi.hygiene + 40)
    events.append(f"🛁 *Купание:* {tamagochi.name} помылся{'ась' if tamagochi.gender == Gender.GIRL else ''} в {bath_type}")
    
    # 11. СОН
    tamagochi.is_sleeping = True
    tamagochi.energy = min(100, tamagochi.energy + 30)
    tamagochi.health = min(100, tamagochi.health + 8)
    events.append(f"🌙 *Сон:* {tamagochi.name} лег{'ла' if tamagochi.gender == Gender.GIRL else ''} спать")
    
    # Сохранение
    save_data()
    
    # Формируем ответ
    routine_text = "📅 *ЕЖЕДНЕВНАЯ РУТИНА:*\n\n"
    for i, event in enumerate(events, 1):
        routine_text += f"{i}. {event}\n"
    
    routine_text += f"\n*Итоги дня:*\n"
    routine_text += f"• 🏫 Уроков посещено: {tamagochi.daily_stats['lessons_attended']}\n"
    routine_text += f"• 🍽️ Приемов пищи: {tamagochi.daily_stats['meals_eaten']}\n"
    routine_text += f"• 🎯 Карьерных очков: +{tamagochi.daily_stats['lessons_attended'] * 3}\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🎭 Событие", callback_data="action_event")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        routine_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def care_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "care_menu"):
        return
    
    keyboard = [
        [InlineKeyboardButton("🍼 Покормить", callback_data="care_feed"),
         InlineKeyboardButton("🛁 Помыть", callback_data="care_wash")],
        [InlineKeyboardButton("💤 Уложить спать", callback_data="care_sleep"),
         InlineKeyboardButton("☀️ Разбудить", callback_data="care_wake")],
        [InlineKeyboardButton("💊 Лечить", callback_data="care_heal"),
         InlineKeyboardButton("📚 Учить", callback_data="care_study")],
        [InlineKeyboardButton("🎮 Играть", callback_data="care_play"),
         InlineKeyboardButton("🎨 Творить", callback_data="care_create")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            "👶 *Уход за ребенком:*\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "👶 *Уход за ребенком:*\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_care(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "handle_care"):
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_tamagochi:
        await query.message.edit_text("У вас еще нет ребенка!")
        return
    
    tamagochi = user_tamagochi[user_id]
    action = query.data.split("_")[1]
    
    result_text = ""
    
    if action == "feed":
        if tamagochi.hunger < 20:
            result_text = f"{tamagochi.name} не хочет есть сейчас 🍽️"
        else:
            tamagochi.hunger = max(0, tamagochi.hunger - 40)
            tamagochi.happiness = min(100, tamagochi.happiness + 10)
            tamagochi.health = min(100, tamagochi.health + 5)
            result_text = f"🍼 Вы покормили {tamagochi.name}! Сытость повышена 😋"
            tamagochi.daily_stats["meals_eaten"] += 1
            
    elif action == "wash":
        if tamagochi.hygiene > 90:
            result_text = f"{tamagochi.name} уже чист{'ый' if tamagochi.gender == Gender.BOY else 'ая'} 🧼"
        else:
            tamagochi.hygiene = min(100, tamagochi.hygiene + 50)
            tamagochi.happiness = min(100, tamagochi.happiness + 5)
            if tamagochi.is_sick:
                tamagochi.health = min(100, tamagochi.health + 15)
                tamagochi.is_sick = False
            result_text = f"🛁 Вы помыли {tamagochi.name}! Чистота повышена ✨"
            
    elif action == "sleep":
        if tamagochi.is_sleeping:
            result_text = f"{tamagochi.name} уже спит 💤"
        else:
            tamagochi.is_sleeping = True
            tamagochi.energy = min(100, tamagochi.energy + 30)
            tamagochi.health = min(100, tamagochi.health + 10)
            result_text = f"💤 Вы уложили {tamagochi.name} спать. Энергия восстанавливается 🌙"
            
    elif action == "wake":
        if not tamagochi.is_sleeping:
            result_text = f"{tamagochi.name} уже не спит ☀️"
        else:
            tamagochi.is_sleeping = False
            tamagochi.energy = min(100, tamagochi.energy + 20)
            result_text = f"☀️ Вы разбудили {tamagochi.name}! Начинается новый день! ⏰"
            
    elif action == "heal":
        if not tamagochi.is_sick:
            result_text = f"{tamagochi.name} не болен{'на'} 🏥"
        else:
            tamagochi.is_sick = False
            tamagochi.health = min(100, tamagochi.health + 30)
            tamagochi.happiness = min(100, tamagochi.happiness + 20)
            tamagochi.money -= 20
            result_text = f"💊 Вы вылечили {tamagochi.name}! Здоровье восстановлено ❤️"
            
    elif action == "study":
        if tamagochi.energy < 20:
            result_text = f"{tamagochi.name} слишком устал{' ' if tamagochi.gender == Gender.BOY else 'а '}для учебы 📚"
        else:
            tamagochi.intelligence += random.randint(1, 5)
            tamagochi.skills["учёба"] += 2
            tamagochi.energy = max(0, tamagochi.energy - 15)
            tamagochi.discipline = min(100, tamagochi.discipline + 5)
            tamagochi.career_points += 3
            tamagochi.daily_stats["studied"] += 1
            result_text = f"📚 Вы позанимались с {tamagochi.name}! Интеллект повышен 🧠"
    
    elif action == "play":
        if tamagochi.energy < 15:
            result_text = f"{tamagochi.name} слишком устал{' ' if tamagochi.gender == Gender.BOY else 'а '}для игр 🎮"
        else:
            tamagochi.happiness = min(100, tamagochi.happiness + 25)
            tamagochi.energy = max(0, tamagochi.energy - 10)
            tamagochi.social = min(100, tamagochi.social + 5)
            tamagochi.daily_stats["entertainment"] += 1
            result_text = f"🎮 Вы поиграли с {tamagochi.name}! Настроение улучшено 😊"
            
    elif action == "create":
        tamagochi.creativity = min(100, tamagochi.creativity + 10)
        tamagochi.skills["творчество"] += 2
        tamagochi.happiness = min(100, tamagochi.happiness + 15)
        result_text = f"🎨 {tamagochi.name} занял{'ась' if tamagochi.gender == Gender.GIRL else ''}ся творчеством! 🖌️"
    
    # Обновляем настроение и сохраняем
    tamagochi.update_mood()
    save_data()
    
    # Показываем результат и возвращаем в меню ухода
    await query.message.reply_text(result_text)
    await care_menu(update, context)

async def random_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/event"):
        return
    
    user_id = update.effective_user.id
    
    if user_id not in user_tamagochi:
        await update.message.reply_text("У вас еще нет ребенка!")
        return
    
    tamagochi = user_tamagochi[user_id]
    
    # Получаем случайное событие
    event_text, effect_type, effect_value, points_type, points_value = tamagochi.event_gen.get_life_event(
        tamagochi.name, tamagochi.gender
    )
    
    # Применяем эффекты
    result_text = f"🎭 *СЛУЧАЙНОЕ СОБЫТИЕ:*\n{event_text}\n\n"
    
    if effect_type == "health":
        tamagochi.health = max(0, min(100, tamagochi.health + effect_value))
        result_text += f"❤️ Здоровье: {'+' if effect_value > 0 else ''}{effect_value}\n"
    elif effect_type == "money":
        tamagochi.money += effect_value
        result_text += f"💰 Деньги: {'+' if effect_value > 0 else ''}{effect_value} руб.\n"
    elif effect_type == "intelligence":
        tamagochi.intelligence += effect_value
        result_text += f"🧠 Интеллект: {'+' if effect_value > 0 else ''}{effect_value}\n"
    elif effect_type == "discipline":
        tamagochi.discipline = max(0, min(100, tamagochi.discipline + effect_value))
        result_text += f"⚖️ Дисциплина: {'+' if effect_value > 0 else ''}{effect_value}\n"
    elif effect_type == "social":
        tamagochi.social = max(0, min(100, tamagochi.social + effect_value))
        result_text += f"👥 Общительность: {'+' if effect_value > 0 else ''}{effect_value}\n"
    elif effect_type == "reputation":
        tamagochi.reputation = max(0, min(100, tamagochi.reputation + effect_value))
        result_text += f"⭐ Репутация: {'+' if effect_type == 'reputation' and effect_value > 0 else ''}{effect_value}\n"
    elif effect_type == "creativity":
        tamagochi.creativity = max(0, min(100, tamagochi.creativity + effect_value))
        result_text += f"🎨 Творчество: {'+' if effect_value > 0 else ''}{effect_value}\n"
    
    if points_type == "career":
        tamagochi.career_points += points_value
        result_text += f"🚀 Карьерные очки: +{points_value}\n"
    elif points_type == "criminal":
        tamagochi.criminal_points += points_value
        result_text += f"⚠️ Криминальные очки: +{points_value}\n"
    elif points_type == "happiness":
        tamagochi.happiness = max(0, min(100, tamagochi.happiness + points_value))
        result_text += f"😊 Счастье: {'+' if points_value > 0 else ''}{points_value}\n"
    
    # Обновляем настроение
    tamagochi.update_mood()
    save_data()
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🎭 Еще событие", callback_data="action_event")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def check_destiny(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/destiny"):
        return
    
    user_id = update.effective_user.id
    
    if user_id not in user_tamagochi:
        await update.message.reply_text("У вас еще нет ребенка!")
        return
    
    tamagochi = user_tamagochi[user_id]
    age_years = tamagochi.age_days // 365
    
    if age_years < 13:
        years_left = 13 - age_years
        days_left = years_left * 365
        
        # Прогноз судьбы
        career_ratio = tamagochi.career_points / max(1, tamagochi.age_days)
        criminal_ratio = tamagochi.criminal_points / max(1, tamagochi.age_days)
        
        if criminal_ratio > 0.5:
            prediction = "⚠️ *Тревожный прогноз:* Ребенок движется к проблемам с законом!"
        elif career_ratio > 0.8:
            prediction = "⭐ *Отличный прогноз:* Ребенок на пути к успешной карьере!"
        elif tamagochi.intelligence > 80:
            prediction = "🎓 *Умный ребенок:* Хорошие шансы на получение образования!"
        elif tamagochi.discipline < 30:
            prediction = "😟 *Слабый прогноз:* Нужно больше дисциплины!"
        else:
            prediction = "👤 *Обычная жизнь:* Пока все идет своим чередом."
        
        destiny_text = f"""
🔮 *ПРОВЕРКА СУДЬБЫ {tamagochi.name.upper()}:*

🎂 *Текущий возраст:* {age_years} лет
⏳ *До 13 лет осталось:* {years_left} лет ({days_left} дней)

📊 *ТЕКУЩИЕ ПОКАЗАТЕЛИ:*
• 🚀 Карьерные очки: {tamagochi.career_points}
• ⚠️ Криминальные очки: {tamagochi.criminal_points}
• 🧠 Интеллект: {tamagochi.intelligence}
• ⚖️ Дисциплина: {tamagochi.discipline}
• 💰 Деньги: {tamagochi.money} руб.

📈 *ПРОГНОЗ:* 
{prediction}

💡 *СОВЕТЫ:*
{'- Уделяйте больше внимания учебе!' if tamagochi.career_points < 50 else '- Продолжайте в том же духе!'}
{'- Контролируйте поведение ребенка!' if tamagochi.criminal_points > 30 else '- Поведение в норме.'}
{'- Развивайте социальные навыки!' if tamagochi.social < 40 else '- Социальные навыки хорошие.'}
"""
    else:
        # Определение финальной судьбы в 13 лет
        if tamagochi.career_points > 150 and tamagochi.criminal_points < 30:
            destiny = f"""
🎉 *ПОБЕДА! {tamagochi.name} РАЗБОГАТЕЛ{' ' if tamagochi.gender == Gender.BOY else 'А'}!*

Благодаря отличному воспитанию, {tamagochi.name} стал{' ' if tamagochi.gender == Gender.BOY else 'а '}успешным предпринимателем в 13 лет!
💰 *Состояние:* {tamagochi.money * 100} рублей
🏆 *Достижения:* Основал{'а' if tamagochi.gender == Gender.GIRL else ''} свою IT-компанию
⭐ *Будущее:* Яркая карьера и признание!

*Ваш результат:* Идеальный родитель! 👑
"""
        elif tamagochi.criminal_points > 100:
            destiny = f"""
🚨 *ТРАГЕДИЯ! {tamagochi.name} ПОПАЛ{' ' if tamagochi.gender == Gender.BOY else 'А'} В ТЮРЬМУ!*

Из-за плохого воспитания и множества проступков {tamagochi.name} оказался{'ась' if tamagochi.gender == Gender.GIRL else ''} в исправительной колонии.
😔 *Причина:* {random.choice(['кражи', 'драки', 'вандализм', 'мошенничество'])}
⏳ *Срок:* {random.randint(2, 5)} года
💔 *Родители:* Разочарованы и опечалены...

*Ваш результат:* Провал в воспитании... 😢
"""
        elif tamagochi.health < 30:
            destiny = f"""
🏥 *СЛАБОЕ ЗДОРОВЬЕ!*

{tamagochi.name} часто болел{' ' if tamagochi.gender == Gender.BOY else 'а '}и имеет серьезные проблемы со здоровьем.
❤️ *Здоровье:* {tamagochi.health}/100
💊 *Лечение:* Требуется постоянный медицинский уход
📉 *Перспективы:* Ограниченные возможности

*Ваш результат:* Нужно больше заботиться о здоровье ребенка! 🏥
"""
        elif tamagochi.intelligence > 120:
            destiny = f"""
🎓 *ВУНДЕРКИНД!*

{tamagochi.name} показал{' ' if tamagochi.gender == Gender.BOY else 'а '}выдающиеся интеллектуальные способности!
🧠 *IQ:* {tamagochi.intelligence}
🏆 *Достижения:* Победитель международных олимпиад
🎯 *Будущее:* Стипендия в Гарварде/Оксфорде

*Ваш результат:* Вы воспитали гения! 🧬
"""
        else:
            destiny = f"""
👤 *ОБЫЧНАЯ ЖИЗНЬ*

{tamagochi.name} вырос{' ' if tamagochi.gender == Gender.BOY else 'а '}обычным подростком со своими достоинствами и недостатками.
📊 *Баланс:* Карьера {tamagochi.career_points} / Криминал {tamagochi.criminal_points}
💼 *Работа:* {random.choice(['офисный сотрудник', 'продавец', 'водитель', 'учитель'])}
🏠 *Жизнь:* Стабильная, но не выдающаяся

*Ваш результат:* Средний родитель. Можно было лучше! ⚖️
"""
        
        destiny_text = f"""
🔮 *ФИНАЛЬНАЯ СУДЬБА В 13 ЛЕТ*

{destiny}

📈 *ИТОГОВАЯ СТАТИСТИКА:*
• 🎂 Возраст: {age_years} лет
• 🧠 Интеллект: {tamagochi.intelligence}
• 💰 Деньги: {tamagochi.money} руб.
• ⚖️ Дисциплина: {tamagochi.discipline}
• ⭐ Репутация: {tamagochi.reputation}
• 👥 Друзей: {len(tamagochi.friends)}
• 🏆 Навыков: {sum(tamagochi.skills.values())} очков
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🌅 Продолжить", callback_data="action_daily")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        destiny_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/help"):
        return
    
    help_text = """
🎮 *БОТ-ТАМАГОЧИ "ВИРТУАЛЬНЫЙ РЕБЕНОК"*

🤖 *УПРАВЛЕНИЕ СОСТОЯНИЕМ БОТА:*
/sleep - Уложить бота спать (перестанет отвечать)
/wakeup - Разбудить бота
/status_bot - Проверить состояние бота

👶 *ОСНОВНЫЕ КОМАНДЫ ИГРЫ:*
/start - Создать нового ребенка
/status - Показать состояние ребенка
/daily - Прожить день (утро-вечер)
/care - Уход за ребенком
/event - Случайное жизненное событие
/destiny - Проверить судьбу
/help - Эта справка

👆 *ИЛИ ИСПОЛЬЗУЙТЕ КНОПКИ В МЕНЮ*

👶 *УХОД ЗА РЕБЕНКОМ:*
🍼 Кормить - Уменьшает голод, повышает здоровье
🛁 Мыть - Увеличивает чистоту, лечит болезни
💤 Усыпить - Восстанавливает энергию
☀️ Разбудить - Начать новый день
💊 Лечить - Вылечить болезни, стоит денег
📚 Учить - Повышает интеллект и карьерные очки
🎮 Играть - Повышает настроение и общительность
🎨 Творить - Развивает творческие навыки

📅 *ЕЖЕДНЕВНАЯ РУТИНА:*
1. Пробуждение (с будильником или без)
2. Умывание и гигиена
3. Завтрак
4. Зарядка (если дисциплина высокая)
5. Школа (1-6 уроков или прогулы)
6. Обед
7. Дневные активности (игры, прогулки, кружки)
8. Ужин
9. Вечерние процедуры (ванна/душ)
10. Сон

🎯 *ЦЕЛЬ ИГРЫ:*
Воспитать ребенка к 13 годам так, чтобы он:
✅ *РАЗБОГАТЕЛ* (много карьерных очков)
❌ *НЕ ПОПАЛ В ТЮРЬМУ* (мало криминальных очков)

📊 *ВАЖНЫЕ ПОКАЗАТЕЛИ:*
• ❤️ Здоровье - если упадет до 0, игра окончена
• 😊 Счастье - влияет на настроение и события
• ⚖️ Дисциплина - влияет на успехи в школе
• 🧠 Интеллект - определяет будущие возможности
• 👥 Общительность - помогает заводить друзей
• ⭐ Репутация - влияет на случайные события

💡 *СОВЕТЫ:*
1. Следите за основными показателями (голод, чистота, энергия)
2. Балансируйте учебу и отдых
3. Развивайте разные навыки
4. Участвуйте в случайных событиях
5. Контролируйте дисциплину и поведение

🎭 *СЛУЧАЙНЫЕ СОБЫТИЯ могут:*
• Дать или отнять деньги
• Повысить или понизить характеристики
• Добавить карьерных или криминальных очков
• Изменить репутацию

*Удачи в воспитании вашего виртуального ребенка!* 👨‍👦👩‍👧
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "handle_main_menu"):
        return
    
    query = update.callback_query
    await query.answer()
    
    action = query.data.split("_")[1]
    
    if action == "status":
        await show_status(update, context)
    elif action == "daily":
        await daily_routine(update, context)
    elif action == "care":
        await care_menu(update, context)
    elif action == "event":
        await random_event(update, context)
    elif action == "destiny":
        await check_destiny(update, context)
    elif action == "menu":
        await show_main_menu(update, context)
    elif action == "reset_day":
        user_id = query.from_user.id
        if user_id in user_tamagochi:
            user_tamagochi[user_id].daily_stats = {
                "lessons_attended": 0,
                "meals_eaten": 0,
                "studied": 0,
                "entertainment": 0
            }
            save_data()
            await query.message.reply_text("📊 Дневная статистика сброшена!")
        await show_main_menu(update, context)

def main():
    # Загрузка данных при старте
    load_data()
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики команд (сначала команды управления сном)
    application.add_handler(CommandHandler("sleep", sleep_command))
    application.add_handler(CommandHandler("wakeup", wakeup_command))
    application.add_handler(CommandHandler("status_bot", status_bot_command))
    
    # Обработчики команд игры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(CommandHandler("daily", daily_routine))
    application.add_handler(CommandHandler("event", random_event))
    application.add_handler(CommandHandler("destiny", check_destiny))
    
    # Обработчики сообщений для установки имени
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_name))
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(set_gender, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^action_"))
    application.add_handler(CallbackQueryHandler(handle_care, pattern="^care_"))
    
    # Сохранение данных при завершении
    import atexit
    atexit.register(save_data)
    
    # Запуск бота
    print("🎮 Бот Тамагочи 'Виртуальный ребенок' запущен!")
    print("🤖 Режим сна бота: АКТИВИРОВАН")
    print("💤 Команда /sleep - уложить бота спать")
    print("☀️ Команда /wakeup - разбудить бота")
    print("🚀 Нажмите Ctrl+C для остановки")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
