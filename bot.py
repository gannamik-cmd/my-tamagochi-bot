import logging
import random
import json
import datetime
import os
from enum import Enum
from typing import Dict, List
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
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: Токен бота не найден!")
    exit(1)

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
        events = [
            (f"{name} нашёл{'ла' if gender == Gender.GIRL else ''} на улице кошелек и сдал{'а' if gender == Gender.GIRL else ''} его в полицию", "reputation", 15, "money", 10),
            (f"{name} помог{'ла' if gender == Gender.GIRL else ''} пожилому человеку донести сумки", "social", 10, "reputation", 10),
            (f"{name} выиграл{'а' if gender == Gender.GIRL else ''} школьную олимпиаду", "intelligence", 10, "career", 20),
            (f"{name} получил{'а' if gender == Gender.GIRL else ''} стипендию за хорошую учебу", "money", 50, "discipline", 10),
            (f"{name} подрался{'ась' if gender == Gender.GIRL else ''} с одноклассником", "health", -15, "criminal", 10),
            (f"{name} прогулял{'а' if gender == Gender.GIRL else ''} все уроки", "discipline", -10, "criminal", 15),
            (f"{name} организовал{'а' if gender == Gender.GIRL else ''} вечеринку для друзей", "social", 15, "happiness", 20),
            (f"{name} начал{'а' if gender == Gender.GIRL else ''} вести блог о своих увлечениях", "creativity", 10, "social", 10)
        ]
        return random.choice(events)

# Класс Тамагочи
class Tamagochi:
    def __init__(self, name: str, gender: Gender, owner_id: int):
        self.name = name
        self.gender = gender
        self.owner_id = owner_id
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
        self.rating_points = 0  # Очки для турнирной таблицы
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
            
        if random.random() < 0.1 and self.hygiene < 40:
            self.is_sick = True
            self.health -= 10
            
        if self.hunger < 20 and self.hygiene > 80 and self.energy > 70:
            self.happiness += random.randint(1, 3)
            
        self.health = max(0, min(100, self.health))
        self.hunger = max(0, min(100, self.hunger))
        self.hygiene = max(0, min(100, self.hygiene))
        self.energy = max(0, min(100, self.energy))
        self.happiness = max(0, min(100, self.happiness))
        
        self.update_mood()
    
    def update_rating(self):
        """Обновление рейтинговых очков для турнирной таблицы"""
        self.rating_points = (
            self.career_points * 2 +
            self.intelligence * 3 +
            self.discipline * 2 +
            self.social * 1 +
            self.creativity * 1 -
            self.criminal_points * 5
        )
        return self.rating_points
    
    def to_dict(self):
        return {
            "name": self.name,
            "gender": self.gender.value,
            "owner_id": self.owner_id,
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
            "rating_points": self.rating_points,
            "inventory": self.inventory,
            "friends": self.friends
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        gender = Gender(data["gender"])
        owner_id = data.get("owner_id", 0)
        tamagochi = cls(data["name"], gender, owner_id)
        
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
        tamagochi.rating_points = data.get("rating_points", 0)
        tamagochi.inventory = data["inventory"]
        tamagochi.friends = data["friends"]
        
        return tamagochi

# Турнирная система
class Tournament:
    def __init__(self):
        self.leaderboard = {}  # {user_id: {"name": имя_ребенка, "rating": очки, "owner_name": имя_владельца}}
        self.last_updated = datetime.datetime.now()
    
    def update_player(self, user_id: int, tamagochi: Tamagochi, owner_name: str):
        rating = tamagochi.update_rating()
        self.leaderboard[user_id] = {
            "name": tamagochi.name,
            "rating": rating,
            "owner_name": owner_name,
            "age": tamagochi.age_days // 365,
            "career": tamagochi.career_points,
            "criminal": tamagochi.criminal_points
        }
        self.last_updated = datetime.datetime.now()
    
    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Возвращает отсортированный список лидеров"""
        sorted_players = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1]["rating"],
            reverse=True
        )
        return [(user_id, data) for user_id, data in sorted_players[:limit]]
    
    def get_player_position(self, user_id: int) -> int:
        """Возвращает позицию игрока в турнирной таблице (1-based)"""
        if user_id not in self.leaderboard:
            return 0
        
        sorted_players = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1]["rating"],
            reverse=True
        )
        
        for i, (uid, _) in enumerate(sorted_players, 1):
            if uid == user_id:
                return i
        return 0
    
    def to_dict(self):
        return {
            "leaderboard": self.leaderboard,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        tournament = cls()
        tournament.leaderboard = data.get("leaderboard", {})
        if data.get("last_updated"):
            tournament.last_updated = datetime.datetime.fromisoformat(data["last_updated"])
        return tournament

# Глобальное хранилище данных
user_tamagochi = {}
user_names = {}  # Храним имена пользователей для турнирной таблицы
tournament = Tournament()
user_save_file = "tamagochi_data.json"
tournament_save_file = "tournament_data.json"

def load_data():
    global user_tamagochi, tournament
    try:
        with open(user_save_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for user_id, tam_data in data.items():
                user_tamagochi[int(user_id)] = Tamagochi.from_dict(tam_data)
        logger.info("Данные тамагочи загружены")
    except FileNotFoundError:
        logger.info("Файл данных тамагочи не найден, создаем новый")
    
    try:
        with open(tournament_save_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            tournament = Tournament.from_dict(data)
        logger.info("Данные турнира загружены")
    except FileNotFoundError:
        logger.info("Файл турнира не найден, создаем новый")

def save_data():
    # Сохраняем тамагочи
    data = {}
    for user_id, tamagochi in user_tamagochi.items():
        data[str(user_id)] = tamagochi.to_dict()
    
    with open(user_save_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Сохраняем турнир
    with open(tournament_save_file, 'w', encoding='utf-8') as f:
        json.dump(tournament.to_dict(), f, ensure_ascii=False, indent=2)
    
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

# ====== ТУРНИРНЫЕ КОМАНДЫ ======
async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает турнирную таблицу"""
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/tournament"):
        return
    
    user_id = update.effective_user.id
    
    # Получаем топ-10 игроков
    leaderboard = tournament.get_leaderboard(10)
    
    if not leaderboard:
        await update.message.reply_text("🏆 Турнирная таблица пуста!\nСоздайте ребенка и начните играть!")
        return
    
    # Формируем таблицу
    table_text = "🏆 *ТУРНИРНАЯ ТАБЛИЦА*\n\n"
    table_text += "Место | Ребенок | Владелец | Очки\n"
    table_text += "─" * 50 + "\n"
    
    for i, (uid, data) in enumerate(leaderboard, 1):
        medal = ""
        if i == 1: medal = "🥇 "
        elif i == 2: medal = "🥈 "
        elif i == 3: medal = "🥉 "
        
        table_text += f"{medal}{i}. {data['name']} | {data['owner_name']} | {data['rating']} очков\n"
    
    # Добавляем информацию о текущем игроке
    position = tournament.get_player_position(user_id)
    if position > 0:
        table_text += f"\n📊 *Ваша позиция:* #{position}"
        if user_id in tournament.leaderboard:
            table_text += f"\n👤 Ваш ребенок: {tournament.leaderboard[user_id]['name']}"
            table_text += f"\n🏆 Ваши очки: {tournament.leaderboard[user_id]['rating']}"
    else:
        table_text += "\n📊 Вы еще не в турнирной таблице. Создайте ребенка!"
    
    table_text += f"\n\n🔄 Обновлено: {tournament.last_updated.strftime('%d.%m.%Y %H:%M')}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="action_tournament"),
         InlineKeyboardButton("📊 Мой рейтинг", callback_data="action_rating")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        table_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает рейтинг текущего игрока"""
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/rating"):
        return
    
    user_id = update.effective_user.id
    
    if user_id not in user_tamagochi:
        await update.message.reply_text("У вас еще нет ребенка! Используйте /start для создания.")
        return
    
    tamagochi = user_tamagochi[user_id]
    position = tournament.get_player_position(user_id)
    rating = tamagochi.update_rating()
    
    rating_text = f"""
📊 *ВАШ РЕЙТИНГ*

👤 *Ребенок:* {tamagochi.name}
👑 *Владелец:* {user_names.get(user_id, 'Игрок')}
🏆 *Турнирные очки:* {rating}
🏅 *Место в таблице:* #{position if position > 0 else 'не в таблице'}

📈 *КОМПОНЕНТЫ РЕЙТИНГА:*
• 🚀 Карьерные очки: {tamagochi.career_points} × 2 = {tamagochi.career_points * 2}
• 🧠 Интеллект: {tamagochi.intelligence} × 3 = {tamagochi.intelligence * 3}
• ⚖️ Дисциплина: {tamagochi.discipline} × 2 = {tamagochi.discipline * 2}
• 👥 Социальные: {tamagochi.social} × 1 = {tamagochi.social}
• 🎨 Творчество: {tamagochi.creativity} × 1 = {tamagochi.creativity}
• ⚠️ Криминал: {tamagochi.criminal_points} × -5 = -{tamagochi.criminal_points * 5}

💡 *КАК ПОВЫСИТЬ РЕЙТИНГ:*
1. Учитесь (/daily, /care study) - повышает интеллект
2. Получайте карьерные очки (хорошая учеба, события)
3. Следите за дисциплиной
4. Избегайте криминальных очков (не прогуливайте школу)
"""
    
    keyboard = [
        [InlineKeyboardButton("🏆 Турнирная таблица", callback_data="action_tournament"),
         InlineKeyboardButton("📊 Статус ребенка", callback_data="action_status")],
        [InlineKeyboardButton("🌅 Улучшить рейтинг", callback_data="action_daily"),
         InlineKeyboardButton("🏠 Главное меню", callback_data="action_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        rating_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ====== ОБНОВЛЁННЫЕ КОМАНДЫ БОТА С ПРОВЕРКОЙ СНА ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не спит ли бот
    if not await check_bot_sleep(update, context, "/start"):
        return
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Игрок"
    user_names[user_id] = user_name
    
    if user_id in user_tamagochi:
        await show_status(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("👧 Девочка", callback_data="gender_girl")],
        [InlineKeyboardButton("👦 Мальчик", callback_data="gender_boy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user_name}! Добро пожаловать в игру 'Виртуальный ребенок'!\n\n"
        "Вы становитесь родителем ребенка, который будет расти и развиваться.\n"
        "Теперь доступны соревнования с другими игроками! 🏆\n\n"
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
    user_name = user_names.get(user_id, "Игрок")
    
    if not name or len(name) > 20:
        await update.message.reply_text("Имя должно быть от 1 до 20 символов. Попробуйте еще раз:")
        return
    
    gender = context.user_data.get('gender', Gender.BOY)
    tamagochi = Tamagochi(name, gender, user_id)
    user_tamagochi[user_id] = tamagochi
    
    # Добавляем в турнирную таблицу
    tournament.update_player(user_id, tamagochi, user_name)
    
    save_data()
    
    await update.message.reply_text(
        f"🎉 Поздравляем, {user_name}! У вас родился{'ся' if gender == Gender.BOY else 'ась'} {name}!\n\n"
        f"Теперь вы можете ухаживать за своим ребенком и соревноваться с другими!\n\n"
        f"🏆 *Новые турнирные команды:*\n"
        f"/tournament - турнирная таблица\n"
        f"/rating - ваш рейтинг\n\n"
        f"🤖 *Управление ботом:*\n"
        f"/sleep - уложить бота спать\n"
        f"/wakeup - разбудить бота\n"
        f"/status_bot - состояние бота\n\n"
        f"🎮 *Основные команды игры:*\n"
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
        [InlineKeyboardButton("🏆 Турнир", callback_data="action_tournament")],
        [InlineKeyboardButton("📈 Рейтинг", callback_data="action_rating")],
        [InlineKeyboardButton("🔮 Судьба", callback_data="action_destiny")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "🏆 *Главное меню с турниром:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🏆 *Главное меню с турниром:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
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
    
    # Обновляем естественные изменения
    tamagochi.natural_changes()
    
    age_years = tamagochi.age_days // 365
    age_months = (tamagochi.age_days % 365) // 30
    
    # Индикаторы прогресса
    def progress_bar(value, max_value=100):
        filled = int(value / max_value * 10)
        return "█" * filled + "░" * (10 - filled)
    
    # Получаем позицию в турнире
    position = tournament.get_player_position(user_id)
    rating = tamagochi.update_rating()
    
    # Показываем состояние бота в статусе
    global BOT_IS_SLEEPING
    bot_status = "💤 Спит" if BOT_IS_SLEEPING else "☀️ Бодрствует"
    
    status_text = f"""
👤 *{tamagochi.name}* ({tamagochi.gender.value})
👑 Владелец: {user_names.get(user_id, 'Игрок')}
🤖 Состояние бота: {bot_status}
🏆 Рейтинг: {rating} очков (Место #{position if position > 0 else 'не в таблице'})

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
• 🏆 Турнирные очки: {rating}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="action_status"),
         InlineKeyboardButton("🏆 Турнир", callback_data="action_tournament")],
        [InlineKeyboardButton("🌅 Улучшить рейтинг", callback_data="action_daily"),
         InlineKeyboardButton("📈 Мой рейтинг", callback_data="action_rating")],
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
    
    # Обновляем турнирную таблицу
    if user_id in user_names:
        tournament.update_player(user_id, tamagochi, user_names[user_id])
        save_data()

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
    
    # Обновляем турнирную таблицу
    tournament.update_player(user_id, tamagochi, user_names.get(user_id, "Игрок"))
    
    # Сохранение
    save_data()
    
    # Формируем ответ
    routine_text = "📅 *ЕЖЕДНЕВНАЯ РУТИНА:*\n\n"
    for i, event in enumerate(events, 1):
        routine_text += f"{i}. {event}\n"
    
    # Показываем изменение рейтинга
    old_rating = tamagochi.rating_points
    new_rating = tamagochi.update_rating()
    rating_change = new_rating - old_rating
    
    routine_text += f"\n*Итоги дня:*\n"
    routine_text += f"• 🏫 Уроков посещено: {tamagochi.daily_stats['lessons_attended']}\n"
    routine_text += f"• 🍽️ Приемов пищи: {tamagochi.daily_stats['meals_eaten']}\n"
    routine_text += f"• 🎯 Карьерных очков: +{tamagochi.daily_stats['lessons_attended'] * 3}\n"
    routine_text += f"• 🏆 Рейтинг: {new_rating} очков "
    if rating_change > 0:
        routine_text += f"(+{rating_change} 📈)"
    elif rating_change < 0:
        routine_text += f"({rating_change} 📉)"
    else:
        routine_text += "(без изменений)"
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🏆 Турнир", callback_data="action_tournament")],
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
    
    # Обновляем настроение, рейтинг и сохраняем
    tamagochi.update_mood()
    tamagochi.update_rating()
    
    # Обновляем турнирную таблицу
    if user_id in user_names:
        tournament.update_player(user_id, tamagochi, user_names[user_id])
    
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
    
    # Обновляем настроение и рейтинг
    tamagochi.update_mood()
    tamagochi.update_rating()
    
    # Обновляем турнирную таблицу
    if user_id in user_names:
        tournament.update_player(user_id, tamagochi, user_names[user_id])
    
    save_data()
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🏆 Турнир", callback_data="action_tournament")],
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
    
    # Обновляем рейтинг перед проверкой судьбы
    rating = tamagochi.update_rating()
    position = tournament.get_player_position(user_id)
    
    if age_years < 13:
        years_left = 13 - age_years
        days_left = years_left * 365
        
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
• 🏆 Турнирные очки: {rating} (Место #{position if position > 0 else 'не в таблице'})

💡 *СОВЕТЫ ДЛЯ УСПЕХА:*
{'- Уделяйте больше внимания учебе!' if tamagochi.career_points < 50 else '- Продолжайте в том же духе!'}
{'- Контролируйте поведение ребенка!' if tamagochi.criminal_points > 30 else '- Поведение в норме.'}
{'- Развивайте социальные навыки!' if tamagochi.social < 40 else '- Социальные навыки хорошие.'}
{'- Участвуйте в турнире!' if position == 0 else f'- Ваше место в турнире: #{position}'}
"""
    else:
        # Определение финальной судьбы в 13 лет
        rating = tamagochi.update_rating()
        position = tournament.get_player_position(user_id)
        
        if tamagochi.career_points > 150 and tamagochi.criminal_points < 30:
            destiny = f"""
🎉 *ПОБЕДА! {tamagochi.name} РАЗБОГАТЕЛ{' ' if tamagochi.gender == Gender.BOY else 'А'}!*

Благодаря отличному воспитанию, {tamagochi.name} стал{' ' if tamagochi.gender == Gender.BOY else 'а '}успешным предпринимателем в 13 лет!
💰 *Состояние:* {tamagochi.money * 100} рублей
🏆 *Достижения:* Основал{'а' if tamagochi.gender == Gender.GIRL else ''} свою IT-компанию
⭐ *Будущее:* Яркая карьера и признание!

*Турнирный результат:* {rating} очков (Место #{position if position > 0 else 'не в таблице'})
*Ваш результат:* Идеальный родитель! 👑
"""
        elif tamagochi.criminal_points > 100:
            destiny = f"""
🚨 *ТРАГЕДИЯ! {tamagochi.name} ПОПАЛ{' ' if tamagochi.gender == Gender.BOY else 'А'} В ТЮРЬМУ!*

Из-за плохого воспитания и множества проступков {tamagochi.name} оказался{'ась' if tamagochi.gender == Gender.GIRL else ''} в исправительной колонии.
😔 *Причина:* {random.choice(['кражи', 'драки', 'вандализм', 'мошенничество'])}
⏳ *Срок:* {random.randint(2, 5)} года
💔 *Родители:* Разочарованы и опечалены...

*Турнирный результат:* {rating} очков (Место #{position if position > 0 else 'не в таблице'})
*Ваш результат:* Провал в воспитании... 😢
"""
        elif tamagochi.health < 30:
            destiny = f"""
🏥 *СЛАБОЕ ЗДОРОВЬЕ!*

{tamagochi.name} часто болел{' ' if tamagochi.gender == Gender.BOY else 'а '}и имеет серьезные проблемы со здоровьем.
❤️ *Здоровье:* {tamagochi.health}/100
💊 *Лечение:* Требуется постоянный медицинский уход
📉 *Перспективы:* Ограниченные возможности

*Турнирный результат:* {rating} очков (Место #{position if position > 0 else 'не в таблице'})
*Ваш результат:* Нужно больше заботиться о здоровье ребенка! 🏥
"""
        elif tamagochi.intelligence > 120:
            destiny = f"""
🎓 *ВУНДЕРКИНД!*

{tamagochi.name} показал{' ' if tamagochi.gender == Gender.BOY else 'а '}выдающиеся интеллектуальные способности!
🧠 *IQ:* {tamagochi.intelligence}
🏆 *Достижения:* Победитель международных олимпиад
🎯 *Будущее:* Стипендия в Гарварде/Оксфорде

*Турнирный результат:* {rating} очков (Место #{position if position > 0 else 'не в таблице'})
*Ваш результат:* Вы воспитали гения! 🧬
"""
        else:
            destiny = f"""
👤 *ОБЫЧНАЯ ЖИЗНЬ*

{tamagochi.name} вырос{' ' if tamagochi.gender == Gender.BOY else 'а '}обычным подростком со своими достоинствами и недостатками.
📊 *Баланс:* Карьера {tamagochi.career_points} / Криминал {tamagochi.criminal_points}
💼 *Работа:* {random.choice(['офисный сотрудник', 'продавец', 'водитель', 'учитель'])}
🏠 *Жизнь:* Стабильная, но не выдающаяся

*Турнирный результат:* {rating} очков (Место #{position if position > 0 else 'не в таблице'})
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
• 🏅 Турнирные очки: {rating}
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="action_status"),
         InlineKeyboardButton("🏆 Турнир", callback_data="action_tournament")],
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

🏆 *ТУРНИРНЫЕ КОМАНДЫ:*
/tournament - Турнирная таблица (топ-10 игроков)
/rating - Ваш рейтинг и компоненты очков

👶 *ОСНОВНЫЕ КОМАНДЫ ИГРЫ:*
/start - Создать нового ребенка
/status - Показать состояние ребенка
/daily - Прожить день (утро-вечер)
/care - Уход за ребенком
/event - Случайное жизненное событие
/destiny - Проверить судьбу
/help - Эта справка

👆 *ИЛИ ИСПОЛЬЗУЙТЕ КНОПКИ В МЕНЮ*

🏆 *КАК РАБОТАЕТ ТУРНИР:*
Рейтинг = (Карьера×2 + Интеллект×3 + Дисциплина×2 + Социальные×1 + Творчество×1 - Криминал×5)
• Чем выше рейтинг - тем выше место в таблице
• Турнир обновляется после каждого действия
• Все игроки в одном чате соревнуются между собой

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
✅ *ЗАНЯЛ ВЫСОКОЕ МЕСТО В ТУРНИРЕ*
❌ *НЕ ПОПАЛ В ТЮРЬМУ* (мало криминальных очков)

*Удачи в воспитании и победы в турнире!* 👨‍👦👩‍👧🏆
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
    elif action == "tournament":
        await tournament_command(update, context)
    elif action == "rating":
        await rating_command(update, context)
    elif action == "menu":
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
    
    # Турнирные команды
    application.add_handler(CommandHandler("tournament", tournament_command))
    application.add_handler(CommandHandler("rating", rating_command))
    
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
    print("🏆 Турнирная система: АКТИВИРОВАНА")
    print("💤 Команда /sleep - уложить бота спать")
    print("🏆 Команда /tournament - турнирная таблица")
    print("🚀 Нажмите Ctrl+C для остановки")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
