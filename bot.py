import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Перечисления состояний
class Gender(Enum):
    BOY = "мальчик"
    GIRL = "девочка"

class Action(Enum):
    WAKE_UP = "проснуться"
    WASH = "умыться"
    BREAKFAST = "завтракать"
    EXERCISE = "зарядка"
    MAKE_BED = "заправить кровать"
    READ = "читать книги"
    SCHOOL = "школа"
    LUNCH = "обед"
    DINNER = "ужин"
    BATH = "ванна"
    SHOWER = "душ"
    COMPUTER = "игры на компьютере"
    DRAW = "рисовать"
    VISIT = "ходить в гости"
    WALK = "гулять"
    CINEMA = "кинотеатр"
    MUSEUM = "музей"
    EXHIBITION = "выставка"
    THEATER = "театр"
    TUTOR = "репетитор"
    PARTY = "вечеринка"
    SLEEPOVER = "ночевка"
    BAKE = "печь печенье"
    FIGHT = "драться"
    LOVE = "влюбляться"
    BLOG = "вести блог"
    CHAT = "общаться"
    SLEEP = "спать"

@dataclass
class Tamagotchi:
    user_id: int
    name: str
    gender: Gender
    age: int = 0  # в годах
    health: int = 100
    happiness: int = 100
    intelligence: int = 50
    money: int = 0
    reputation: int = 50
    last_action: Optional[str] = None
    is_sleeping: bool = True
    created_at: datetime = None
    actions_history: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.actions_history is None:
            self.actions_history = []
    
    def to_dict(self):
        data = asdict(self)
        data['gender'] = self.gender.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        data['gender'] = Gender(data['gender'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class TamagotchiGame:
    def __init__(self):
        self.tamagotchis: Dict[int, Tamagotchi] = {}
        self.tournament_scores = defaultdict(int)
    
    def create_tamagotchi(self, user_id: int, name: str, gender: Gender) -> Tamagotchi:
        """Создать нового тамагочи"""
        tamagotchi = Tamagotchi(
            user_id=user_id,
            name=name,
            gender=gender
        )
        self.tamagotchis[user_id] = tamagotchi
        self.update_tournament_score(user_id)
        return tamagotchi
    
    def get_tamagotchi(self, user_id: int) -> Optional[Tamagotchi]:
        """Получить тамагочи пользователя"""
        return self.tamagotchis.get(user_id)
    
    def perform_action(self, user_id: int, action: Action) -> str:
        """Выполнить действие и вернуть результат"""
        tamagotchi = self.get_tamagotchi(user_id)
        if not tamagotchi:
            return "У вас нет тамагочи! Создайте его командой /start"
        
        if tamagotchi.is_sleeping and action != Action.WAKE_UP:
            return f"{tamagotchi.name} спит! Разбудите его командой /wakeup"
        
        result = ""
        
        # Обновляем время последнего действия
        tamagotchi.last_action = action.value
        
        # В зависимости от действия меняем характеристики
        if action == Action.WAKE_UP:
            if not tamagotchi.is_sleeping:
                return f"{tamagotchi.name} уже не спит!"
            tamagotchi.is_sleeping = False
            tamagotchi.happiness += random.randint(5, 15)
            result = f"🌅 {tamagotchi.name} проснулся(ась)!"
            
        elif action == Action.WASH:
            tamagotchi.health += random.randint(2, 5)
            result = f"🚿 {tamagotchi.name} умылся(ась)."
            
        elif action == Action.BREAKFAST:
            tamagotchi.health += random.randint(5, 10)
            result = f"🍳 {tamagotchi.name} позавтракал(а)."
            
        elif action == Action.EXERCISE:
            tamagotchi.health += random.randint(10, 15)
            result = f"💪 {tamagotchi.name} сделал(а) зарядку."
            
        elif action == Action.MAKE_BED:
            tamagotchi.happiness += random.randint(3, 7)
            result = f"🛏️ {tamagotchi.name} заправил(а) кровать."
            
        elif action == Action.READ:
            tamagotchi.intelligence += random.randint(5, 15)
            result = f"📚 {tamagotchi.name} читает книгу."
            
        elif action == Action.SCHOOL:
            lessons = random.randint(1, 6)
            tamagotchi.intelligence += random.randint(10, 20)
            if lessons >= 4:
                result = f"🏫 {tamagotchi.name} отлично учился(ась) в школе ({lessons} уроков)!"
            else:
                result = f"😴 {tamagotchi.name} прогулял(а) школу ({lessons} уроков)!"
            
        elif action == Action.LUNCH:
            tamagotchi.health += random.randint(5, 10)
            result = f"🍝 {tamagotchi.name} пообедал(а)."
            
        elif action == Action.DINNER:
            tamagotchi.health += random.randint(5, 10)
            result = f"🍽️ {tamagotchi.name} поужинал(а)."
            
        elif action == Action.BATH:
            tamagotchi.health += random.randint(8, 12)
            result = f"🛁 {tamagotchi.name} принимает ванну."
            
        elif action == Action.SHOWER:
            tamagotchi.health += random.randint(5, 8)
            result = f"🚿 {tamagotchi.name} принимает душ."
            
        elif action == Action.COMPUTER:
            tamagotchi.happiness += random.randint(10, 20)
            result = f"🎮 {tamagotchi.name} играет на компьютере."
            
        elif action == Action.DRAW:
            tamagotchi.happiness += random.randint(5, 15)
            result = f"🎨 {tamagotchi.name} рисует."
            
        elif action == Action.VISIT:
            tamagotchi.happiness += random.randint(15, 25)
            result = f"🏡 {tamagotchi.name} ходит в гости."
            
        elif action == Action.WALK:
            tamagotchi.health += random.randint(5, 10)
            result = f"🚶 {tamagotchi.name} гуляет на улице."
            
        elif action == Action.CINEMA:
            tamagotchi.happiness += random.randint(10, 20)
            result = f"🎬 {tamagotchi.name} идет в кинотеатр."
            
        elif action == Action.MUSEUM:
            tamagotchi.intelligence += random.randint(15, 25)
            result = f"🏛️ {tamagotchi.name} посещает музей."
            
        elif action == Action.EXHIBITION:
            tamagotchi.intelligence += random.randint(10, 20)
            result = f"🖼️ {tamagotchi.name} на выставке."
            
        elif action == Action.THEATER:
            tamagotchi.intelligence += random.randint(12, 22)
            result = f"🎭 {tamagotchi.name} в театре."
            
        elif action == Action.TUTOR:
            tamagotchi.intelligence += random.randint(20, 30)
            result = f"👨‍🏫 {tamagotchi.name} занимается с репетитором."
            
        elif action == Action.PARTY:
            tamagotchi.happiness += random.randint(25, 35)
            result = f"🎉 {tamagotchi.name} устраивает вечеринку!"
            
        elif action == Action.SLEEPOVER:
            tamagotchi.happiness += random.randint(20, 30)
            result = f"🌙 {tamagotchi.name} устраивает ночевку."
            
        elif action == Action.BAKE:
            tamagotchi.happiness += random.randint(10, 20)
            result = f"🍪 {tamagotchi.name} печет печенье."
            
        elif action == Action.FIGHT:
            tamagotchi.happiness -= random.randint(15, 25)
            tamagotchi.reputation -= random.randint(10, 20)
            result = f"👊 {tamagotchi.name} подрался(ась)."
            
        elif action == Action.LOVE:
            tamagotchi.happiness += random.randint(30, 40)
            result = f"❤️ {tamagotchi.name} влюбился(ась)!"
            
        elif action == Action.BLOG:
            tamagotchi.intelligence += random.randint(5, 10)
            tamagotchi.money += random.randint(10, 50)
            result = f"📱 {tamagotchi.name} ведет блог."
            
        elif action == Action.CHAT:
            tamagotchi.happiness += random.randint(5, 15)
            result = f"💬 {tamagotchi.name} общается с друзьями."
            
        elif action == Action.SLEEP:
            if tamagotchi.is_sleeping:
                return f"{tamagotchi.name} уже спит!"
            tamagotchi.is_sleeping = True
            tamagotchi.health += random.randint(10, 20)
            
            # Проверяем дневные активности
            if len([a for a in tamagotchi.actions_history if "школа" in a or "читает" in a]) > 0:
                money_earned = random.randint(20, 50)
                tamagotchi.money += money_earned
                result = f"💤 {tamagotchi.name} ложится спать. Хороший день! +{money_earned}💰"
            else:
                result = f"💤 {tamagotchi.name} ложится спать."
        
        # Ограничиваем значения характеристик
        tamagotchi.health = max(0, min(100, tamagotchi.health))
        tamagotchi.happiness = max(0, min(100, tamagotchi.happiness))
        tamagotchi.intelligence = max(0, min(100, tamagotchi.intelligence))
        tamagotchi.reputation = max(0, min(100, tamagotchi.reputation))
        tamagotchi.money = max(0, tamagotchi.money)
        
        # Добавляем действие в историю
        tamagotchi.actions_history.append(action.value)
        if len(tamagotchi.actions_history) > 10:
            tamagotchi.actions_history.pop(0)
        
        # Обновляем турнирный счет
        self.update_tournament_score(user_id)
        
        return result
    
    def update_tournament_score(self, user_id: int):
        """Обновить счет в турнире для пользователя"""
        tamagotchi = self.get_tamagotchi(user_id)
        if tamagotchi:
            score = (
                tamagotchi.intelligence * 2 +
                tamagotchi.money // 5 +
                tamagotchi.reputation * 3 +
                tamagotchi.health +
                tamagotchi.happiness * 2
            )
            self.tournament_scores[user_id] = score
    
    def get_leaderboard(self) -> str:
        """Получить турнирную таблицу"""
        if not self.tournament_scores:
            return "🏆 Турнирная таблица пуста! Создайте тамагочи и начните играть!"
        
        leaderboard = "🏆 ТУРНИРНАЯ ТАБЛИЦА 🏆\n\n"
        
        # Сортируем по очкам
        sorted_scores = sorted(
            self.tournament_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, (user_id, score) in enumerate(sorted_scores[:10]):
            tamagotchi = self.get_tamagotchi(user_id)
            if tamagotchi:
                medal = medals[i] if i < len(medals) else f"{i+1}."
                leaderboard += f"{medal} {tamagotchi.name}: {score} очков\n"
        
        return leaderboard

# Инициализация игры
game = TamagotchiGame()

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    if game.get_tamagotchi(user_id):
        await update.message.reply_text(
            "У вас уже есть тамагочи! Используйте /status чтобы посмотреть состояние."
        )
        return
    
    await update.message.reply_text(
        "👋 Добро пожаловать в игру Тамагочи!\n"
        "Вырастите своего виртуального ребенка!\n\n"
        "Выберите пол вашего ребенка:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👦 Мальчик", callback_data="gender_boy"),
                InlineKeyboardButton("👧 Девочка", callback_data="gender_girl")
            ]
        ])
    )

async def create_tamagotchi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание тамагочи после выбора пола"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    gender = Gender.BOY if query.data == "gender_boy" else Gender.GIRL
    
    # Запрашиваем имя
    context.user_data['creating_gender'] = gender
    await query.edit_message_text(
        f"Вы выбрали {gender.value}! 👶\n"
        "Введите имя для вашего тамагочи (2-15 символов):"
    )

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка имени тамагочи"""
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    if not (2 <= len(name) <= 15):
        await update.message.reply_text("Имя должно быть от 2 до 15 символов!")
        return
    
    if 'creating_gender' not in context.user_data:
        await update.message.reply_text("Сначала выберите пол командой /start")
        return
    
    gender = context.user_data['creating_gender']
    tamagotchi = game.create_tamagotchi(user_id, name, gender)
    
    await update.message.reply_text(
        f"🎉 Поздравляем! Вы создали {gender.value} по имени {name}!\n\n"
        f"📋 Основные команды:\n"
        f"/status - состояние тамагочи\n"
        f"/actions - доступные действия\n"
        f"/wakeup - разбудить (если спит)\n"
        f"/sleep - уложить спать\n"
        f"/leaderboard - турнирная таблица\n"
        f"/help - подробная справка"
    )
    
    del context.user_data['creating_gender']

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус тамагочи"""
    user_id = update.effective_user.id
    tamagotchi = game.get_tamagotchi(user_id)
    
    if not tamagotchi:
        await update.message.reply_text("У вас нет тамагочи! Создайте его командой /start")
        return
    
    # Полоски прогресса
    def progress_bar(value, max_value=100):
        filled = int(value / max_value * 10)
        return '█' * filled + '░' * (10 - filled)
    
    status_text = (
        f"👤 {tamagotchi.name} ({tamagotchi.gender.value})\n"
        f"📅 Возраст: {tamagotchi.age} лет\n"
        f"❤️ Здоровье: {progress_bar(tamagotchi.health)} {tamagotchi.health}/100\n"
        f"😊 Счастье: {progress_bar(tamagotchi.happiness)} {tamagotchi.happiness}/100\n"
        f"🧠 Интеллект: {progress_bar(tamagotchi.intelligence)} {tamagotchi.intelligence}/100\n"
        f"💰 Деньги: {tamagotchi.money} руб.\n"
        f"⭐ Репутация: {progress_bar(tamagotchi.reputation)} {tamagotchi.reputation}/100\n"
        f"💤 Состояние: {'Спит 😴' if tamagotchi.is_sleeping else 'Бодрствует ☀️'}\n"
    )
    
    if tamagotchi.last_action:
        status_text += f"📝 Последнее действие: {tamagotchi.last_action}\n"
    
    # Показываем последние 3 действия
    if tamagotchi.actions_history:
        status_text += "\n📜 Последние действия:\n"
        for action in tamagotchi.actions_history[-3:]:
            status_text += f"  • {action}\n"
    
    await update.message.reply_text(status_text)

async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбудить тамагочи"""
    user_id = update.effective_user.id
    result = game.perform_action(user_id, Action.WAKE_UP)
    await update.message.reply_text(result)

async def sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Уложить тамагочи спать"""
    user_id = update.effective_user.id
    result = game.perform_action(user_id, Action.SLEEP)
    await update.message.reply_text(result)

async def show_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные действия"""
    user_id = update.effective_user.id
    tamagotchi = game.get_tamagotchi(user_id)
    
    if not tamagotchi:
        await update.message.reply_text("У вас нет тамагочи! Создайте его командой /start")
        return
    
    if tamagotchi.is_sleeping:
        keyboard = [
            [InlineKeyboardButton("🌅 Разбудить", callback_data="action_wake_up")],
            [InlineKeyboardButton("📊 Статус", callback_data="show_status")]
        ]
        text = f"{tamagotchi.name} спит! 💤"
    else:
        keyboard = [
            [
                InlineKeyboardButton("🚿 Умыться", callback_data="action_wash"),
                InlineKeyboardButton("🍳 Завтрак", callback_data="action_breakfast")
            ],
            [
                InlineKeyboardButton("💪 Зарядка", callback_data="action_exercise"),
                InlineKeyboardButton("🛏️ Кровать", callback_data="action_make_bed")
            ],
            [
                InlineKeyboardButton("📚 Читать", callback_data="action_read"),
                InlineKeyboardButton("🏫 Школа", callback_data="action_school")
            ],
            [
                InlineKeyboardButton("🍝 Обед", callback_data="action_lunch"),
                InlineKeyboardButton("🍽️ Ужин", callback_data="action_dinner")
            ],
            [
                InlineKeyboardButton("🛁 Ванна", callback_data="action_bath"),
                InlineKeyboardButton("🎮 Играть", callback_data="action_computer")
            ],
            [
                InlineKeyboardButton("🚶 Гулять", callback_data="action_walk"),
                InlineKeyboardButton("🎉 Вечеринка", callback_data="action_party")
            ],
            [
                InlineKeyboardButton("📊 Статус", callback_data="show_status"),
                InlineKeyboardButton("💤 Спать", callback_data="action_sleep")
            ]
        ]
        text = f"Выберите действие для {tamagotchi.name}:"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "show_status":
        await show_status_callback(update, context)
        return
    
    action_name = query.data.replace("action_", "")
    
    try:
        action = Action[action_name.upper()]
        result = game.perform_action(user_id, action)
        
        # Добавляем кнопку для новых действий
        keyboard = [[
            InlineKeyboardButton("📋 Еще действия", callback_data="more_actions"),
            InlineKeyboardButton("📊 Статус", callback_data="show_status")
        ]]
        
        await query.edit_message_text(
            f"{result}\n\nЧто дальше?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except KeyError:
        await query.edit_message_text("Неизвестное действие!")

async def show_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус через callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    tamagotchi = game.get_tamagotchi(user_id)
    
    if not tamagotchi:
        await query.edit_message_text("У вас нет тамагочи!")
        return
    
    # Полоски прогресса
    def progress_bar(value, max_value=100):
        filled = int(value / max_value * 10)
        return '█' * filled + '░' * (10 - filled)
    
    status_text = (
        f"👤 {tamagotchi.name} ({tamagotchi.gender.value})\n"
        f"❤️ Здоровье: {progress_bar(tamagotchi.health)} {tamagotchi.health}/100\n"
        f"😊 Счастье: {progress_bar(tamagotchi.happiness)} {tamagotchi.happiness}/100\n"
        f"🧠 Интеллект: {progress_bar(tamagotchi.intelligence)} {tamagotchi.intelligence}/100\n"
        f"💰 Деньги: {tamagotchi.money} руб.\n"
        f"⭐ Репутация: {progress_bar(tamagotchi.reputation)} {tamagotchi.reputation}/100\n"
    )
    
    # Добавляем кнопки действий
    keyboard = [[
        InlineKeyboardButton("📋 Действия", callback_data="more_actions"),
        InlineKeyboardButton("🏆 Лидерборд", callback_data="show_leaderboard")
    ]]
    
    await query.edit_message_text(
        status_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def more_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать еще действий"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    tamagotchi = game.get_tamagotchi(user_id)
    
    if not tamagotchi:
        await query.edit_message_text("У вас нет тамагочи!")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🎨 Рисовать", callback_data="action_draw"),
            InlineKeyboardButton("🏡 В гости", callback_data="action_visit")
        ],
        [
            InlineKeyboardButton("🎬 Кино", callback_data="action_cinema"),
            InlineKeyboardButton("🏛️ Музей", callback_data="action_museum")
        ],
        [
            InlineKeyboardButton("🖼️ Выставка", callback_data="action_exhibition"),
            InlineKeyboardButton("🎭 Театр", callback_data="action_theater")
        ],
        [
            InlineKeyboardButton("👨‍🏫 Репетитор", callback_data="action_tutor"),
            InlineKeyboardButton("🌙 Ночевка", callback_data="action_sleepover")
        ],
        [
            InlineKeyboardButton("🍪 Печь", callback_data="action_bake"),
            InlineKeyboardButton("❤️ Влюбиться", callback_data="action_love")
        ],
        [
            InlineKeyboardButton("📱 Блог", callback_data="action_blog"),
            InlineKeyboardButton("💬 Общаться", callback_data="action_chat")
        ],
        [
            InlineKeyboardButton("📊 Статус", callback_data="show_status"),
            InlineKeyboardButton("🏆 Лидерборд", callback_data="show_leaderboard")
        ]
    ]
    
    await query.edit_message_text(
        f"Дополнительные действия для {tamagotchi.name}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать лидерборд через callback"""
    query = update.callback_query
    await query.answer()
    
    leaderboard_text = game.get_leaderboard()
    
    keyboard = [[
        InlineKeyboardButton("📋 Действия", callback_data="more_actions"),
        InlineKeyboardButton("📊 Мой статус", callback_data="show_status")
    ]]
    
    await query.edit_message_text(
        leaderboard_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать турнирную таблицу"""
    leaderboard_text = game.get_leaderboard()
    await update.message.reply_text(leaderboard_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    help_text = (
        "📚 КОМАНДЫ БОТА ТАМАГОЧИ 📚\n\n"
        
        "🎮 ОСНОВНЫЕ КОМАНДЫ:\n"
        "/start - создать нового тамагочи\n"
        "/status - показать состояние вашего тамагочи\n"
        "/actions - показать доступные действия\n"
        "/wakeup - разбудить тамагочи\n"
        "/sleep - уложить тамагочи спать\n"
        "/leaderboard - показать турнирную таблицу\n"
        "/help - эта справка\n\n"
        
        "🎯 ЦЕЛЬ ИГРЫ:\n"
        "Заботьтесь о своем тамагочи, развивайте его характеристики\n"
        "и соревнуйтесь с другими игроками в турнирной таблице!\n\n"
        
        "📈 ХАРАКТЕРИСТИКИ:\n"
        "❤️ Здоровье - влияет на выживаемость\n"
        "😊 Счастье - эмоциональное состояние\n"
        "🧠 Интеллект - умственные способности\n"
        "💰 Деньги - финансовое состояние\n"
        "⭐ Репутация - социальный статус\n\n"
        
        "🏆 ТУРНИРНАЯ ТАБЛИЦА:\n"
        "Соревнуйтесь с другими игроками!\n"
        "Очки начисляются за все характеристики.\n\n"
        
        "💡 СОВЕТЫ:\n"
        "1. Балансируйте между работой и отдыхом\n"
        "2. Развивайте все характеристики\n"
        "3. Участвуйте в социальных активностях\n"
        "4. Не забывайте про сон!"
    )
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Error: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка. Пожалуйста, попробуйте снова."
            )
    except:
        pass

def main():
    """Основная функция запуска бота"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики ошибок
    application.add_error_handler(error_handler)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("wakeup", wakeup))
    application.add_handler(CommandHandler("sleep", sleep))
    application.add_handler(CommandHandler("actions", show_actions))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(create_tamagotchi, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(handle_action, pattern="^action_"))
    application.add_handler(CallbackQueryHandler(show_status_callback, pattern="^show_status$"))
    application.add_handler(CallbackQueryHandler(more_actions, pattern="^more_actions$"))
    application.add_handler(CallbackQueryHandler(show_leaderboard_callback, pattern="^show_leaderboard$"))
    
    # Обработчик текстовых сообщений (для имени)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_name))
    
    # Запускаем polling
    logger.info("Бот запущен...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
