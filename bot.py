import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import asyncio
from dataclasses import dataclass, asdict
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from telegram.error import NetworkError
import nest_asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '')
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
DATA_FILE = 'tamagotchi_data.json'
TOURNAMENT_FILE = 'tournament_data.json'

# Автоматическая обработка вложенных асинхронных вызовов для Render
nest_asyncio.apply()

# Перечисления состояний
class Gender(Enum):
    BOY = "мальчик"
    GIRL = "девочка"

class Mood(Enum):
    HAPPY = "счастливый"
    SAD = "грустный"
    ANGRY = "злой"
    TIRED = "уставший"
    ENERGETIC = "энергичный"

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
    last_action_time: Optional[datetime] = None
    is_sleeping: bool = True
    sleep_time: Optional[datetime] = None
    wake_up_time: Optional[datetime] = None
    created_at: datetime = datetime.now()
    actions_history: List[str] = None
    daily_schedule: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.actions_history is None:
            self.actions_history = []
        if self.daily_schedule is None:
            self.daily_schedule = {
                "woke_up": False,
                "washed": False,
                "breakfast": False,
                "exercised": False,
                "made_bed": False,
                "studied": False,
                "lunch": False,
                "dinner": False,
                "bathed": False
            }
    
    def to_dict(self):
        data = asdict(self)
        data['gender'] = self.gender.value
        data['created_at'] = self.created_at.isoformat()
        if self.last_action_time:
            data['last_action_time'] = self.last_action_time.isoformat()
        if self.sleep_time:
            data['sleep_time'] = self.sleep_time.isoformat()
        if self.wake_up_time:
            data['wake_up_time'] = self.wake_up_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        data['gender'] = Gender(data['gender'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if data.get('last_action_time'):
            data['last_action_time'] = datetime.fromisoformat(data['last_action_time'])
        if data.get('sleep_time'):
            data['sleep_time'] = datetime.fromisoformat(data['sleep_time'])
        if data.get('wake_up_time'):
            data['wake_up_time'] = datetime.fromisoformat(data['wake_up_time'])
        
        return cls(**data)

class TamagotchiGame:
    def __init__(self):
        self.tamagotchis: Dict[int, Tamagotchi] = {}
        self.load_data()
        
    def save_data(self):
        """Сохранить данные в файл"""
        try:
            data = {
                str(user_id): tamagotchi.to_dict()
                for user_id, tamagotchi in self.tamagotchis.items()
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def load_data(self):
        """Загрузить данные из файла"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_id_str, tam_data in data.items():
                    self.tamagotchis[int(user_id_str)] = Tamagotchi.from_dict(tam_data)
                logger.info(f"Loaded {len(self.tamagotchis)} tamagotchis")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def create_tamagotchi(self, user_id: int, name: str, gender: Gender) -> Tamagotchi:
        """Создать нового тамагочи"""
        tamagotchi = Tamagotchi(
            user_id=user_id,
            name=name,
            gender=gender,
            created_at=datetime.now()
        )
        self.tamagotchis[user_id] = tamagotchi
        self.save_data()
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
        now = datetime.now()
        
        # Обновляем время последнего действия
        tamagotchi.last_action = action.value
        tamagotchi.last_action_time = now
        
        # В зависимости от действия меняем характеристики
        if action == Action.WAKE_UP:
            if not tamagotchi.is_sleeping:
                return f"{tamagotchi.name} уже не спит!"
            tamagotchi.is_sleeping = False
            tamagotchi.wake_up_time = now
            tamagotchi.happiness += random.randint(5, 15)
            result = f"{tamagotchi.name} проснулся(ась)! 🌅"
            tamagotchi.daily_schedule["woke_up"] = True
            
        elif action == Action.WASH:
            tamagotchi.health += random.randint(2, 5)
            tamagotchi.happiness += random.randint(1, 3)
            result = f"{tamagotchi.name} умылся(ась). Чистота - залог здоровья! 🚿"
            tamagotchi.daily_schedule["washed"] = True
            
        elif action == Action.BREAKFAST:
            tamagotchi.health += random.randint(5, 10)
            result = f"{tamagotchi.name} позавтракал(а). Вкусно и полезно! 🍳"
            tamagotchi.daily_schedule["breakfast"] = True
            
        elif action == Action.EXERCISE:
            tamagotchi.health += random.randint(10, 15)
            tamagotchi.happiness += random.randint(2, 5)
            result = f"{tamagotchi.name} сделал(а) зарядку. Сила в мышцах! 💪"
            tamagotchi.daily_schedule["exercised"] = True
            
        elif action == Action.MAKE_BED:
            tamagotchi.happiness += random.randint(3, 7)
            tamagotchi.reputation += random.randint(1, 3)
            result = f"{tamagotchi.name} заправил(а) кровать. Порядок в комнате! 🛏️"
            tamagotchi.daily_schedule["made_bed"] = True
            
        elif action == Action.READ:
            tamagotchi.intelligence += random.randint(5, 15)
            result = f"{tamagotchi.name} читает книгу. Знания растут! 📚"
            
        elif action == Action.SCHOOL:
            lessons = random.randint(1, 6)
            tamagotchi.intelligence += random.randint(10, 20)
            tamagotchi.happiness -= random.randint(5, 10)
            if lessons >= 4:
                tamagotchi.reputation += random.randint(3, 7)
                result = f"{tamagotchi.name} отлично учился(ась) в школе ({lessons} уроков)! 🏫"
            else:
                tamagotchi.reputation -= random.randint(2, 5)
                result = f"{tamagotchi.name} прогулял(а) школу ({lessons} уроков пропущено)! 😴"
            tamagotchi.daily_schedule["studied"] = True
            
        elif action == Action.LUNCH:
            tamagotchi.health += random.randint(5, 10)
            result = f"{tamagotchi.name} пообедал(а). 🍝"
            tamagotchi.daily_schedule["lunch"] = True
            
        elif action == Action.DINNER:
            tamagotchi.health += random.randint(5, 10)
            result = f"{tamagotchi.name} поужинал(а). 🍽️"
            tamagotchi.daily_schedule["dinner"] = True
            
        elif action == Action.BATH:
            tamagotchi.health += random.randint(8, 12)
            tamagotchi.happiness += random.randint(5, 10)
            result = f"{tamagotchi.name} принимает ванну. Расслабление! 🛁"
            tamagotchi.daily_schedule["bathed"] = True
            
        elif action == Action.SHOWER:
            tamagotchi.health += random.randint(5, 8)
            result = f"{tamagotchi.name} принимает душ. Освежает! 🚿"
            tamagotchi.daily_schedule["bathed"] = True
            
        elif action == Action.COMPUTER:
            tamagotchi.happiness += random.randint(10, 20)
            tamagotchi.intelligence += random.randint(1, 5)
            tamagotchi.health -= random.randint(2, 5)
            result = f"{tamagotchi.name} играет на компьютере. 🎮"
            
        elif action == Action.DRAW:
            tamagotchi.happiness += random.randint(5, 15)
            tamagotchi.intelligence += random.randint(2, 8)
            result = f"{tamagotchi.name} рисует. Творчество! 🎨"
            
        elif action == Action.VISIT:
            tamagotchi.happiness += random.randint(15, 25)
            tamagotchi.reputation += random.randint(3, 7)
            result = f"{tamagotchi.name} ходит в гости к друзьям. 🏡"
            
        elif action == Action.WALK:
            tamagotchi.health += random.randint(5, 10)
            tamagotchi.happiness += random.randint(5, 15)
            result = f"{tamagotchi.name} гуляет на улице. 🚶‍♂️"
            
        elif action == Action.CINEMA:
            tamagotchi.happiness += random.randint(10, 20)
            tamagotchi.money -= random.randint(50, 150)
            result = f"{tamagotchi.name} идет в кинотеатр. 🎬"
            
        elif action == Action.MUSEUM:
            tamagotchi.intelligence += random.randint(15, 25)
            tamagotchi.happiness += random.randint(5, 10)
            result = f"{tamagotchi.name} посещает музей. 🏛️"
            
        elif action == Action.EXHIBITION:
            tamagotchi.intelligence += random.randint(10, 20)
            tamagotchi.reputation += random.randint(3, 6)
            result = f"{tamagotchi.name} на выставке. 🖼️"
            
        elif action == Action.THEATER:
            tamagotchi.intelligence += random.randint(12, 22)
            tamagotchi.reputation += random.randint(5, 10)
            result = f"{tamagotchi.name} в театре. 🎭"
            
        elif action == Action.TUTOR:
            tamagotchi.intelligence += random.randint(20, 30)
            tamagotchi.money -= random.randint(200, 400)
            tamagotchi.happiness -= random.randint(5, 10)
            result = f"{tamagotchi.name} занимается с репетитором. 👨‍🏫"
            
        elif action == Action.PARTY:
            tamagotchi.happiness += random.randint(25, 35)
            tamagotchi.health -= random.randint(5, 10)
            tamagotchi.reputation += random.randint(8, 15)
            result = f"{tamagotchi.name} устраивает вечеринку! 🎉"
            
        elif action == Action.SLEEPOVER:
            tamagotchi.happiness += random.randint(20, 30)
            result = f"{tamagotchi.name} устраивает ночевку с друзьями. 🌙"
            
        elif action == Action.BAKE:
            tamagotchi.happiness += random.randint(10, 20)
            tamagotchi.reputation += random.randint(2, 5)
            result = f"{tamagotchi.name} печет печенье. Вкусно! 🍪"
            
        elif action == Action.FIGHT:
            tamagotchi.happiness -= random.randint(15, 25)
            tamagotchi.health -= random.randint(10, 20)
            tamagotchi.reputation -= random.randint(10, 20)
            result = f"{tamagotchi.name} подрался(ась). Нехорошо! 👊"
            
        elif action == Action.LOVE:
            tamagotchi.happiness += random.randint(30, 40)
            tamagotchi.reputation += random.randint(5, 10)
            result = f"{tamagotchi.name} влюбился(ась)! ❤️"
            
        elif action == Action.BLOG:
            tamagotchi.intelligence += random.randint(5, 10)
            tamagotchi.reputation += random.randint(3, 8)
            tamagotchi.money += random.randint(10, 50)
            result = f"{tamagotchi.name} ведет блог. 📱"
            
        elif action == Action.CHAT:
            tamagotchi.happiness += random.randint(5, 15)
            tamagotchi.reputation += random.randint(2, 4)
            result = f"{tamagotchi.name} общается с друзьями. 💬"
            
        elif action == Action.SLEEP:
            if tamagotchi.is_sleeping:
                return f"{tamagotchi.name} уже спит!"
            tamagotchi.is_sleeping = True
            tamagotchi.sleep_time = now
            tamagotchi.health += random.randint(10, 20)
            tamagotchi.happiness += random.randint(5, 10)
            
            # Проверяем дневные активности
            completed_tasks = sum(tamagotchi.daily_schedule.values())
            if completed_tasks >= 5:
                tamagotchi.money += random.randint(20, 50)
                result = f"{tamagotchi.name} ложится спать. Хороший день! +{random.randint(20, 50)}💰"
            else:
                result = f"{tamagotchi.name} ложится спать. 💤"
            
            # Сбрасываем дневное расписание
            tamagotchi.daily_schedule = {key: False for key in tamagotchi.daily_schedule}
            
            # Проверяем, не пора ли увеличить возраст
            days_alive = (now - tamagotchi.created_at).days
            if days_alive // 365 > tamagotchi.age and tamagotchi.age < 13:
                tamagotchi.age += 1
                result += f"\n🎉 {tamagotchi.name} исполнилось {tamagotchi.age} лет!"
                
                # В 13 лет подводим итоги
                if tamagotchi.age == 13:
                    result += self._get_final_result(tamagotchi)
        
        # Ограничиваем значения характеристик
        tamagotchi.health = max(0, min(100, tamagotchi.health))
        tamagotchi.happiness = max(0, min(100, tamagotchi.happiness))
        tamagotchi.intelligence = max(0, min(100, tamagotchi.intelligence))
        tamagotchi.reputation = max(0, min(100, tamagotchi.reputation))
        tamagotchi.money = max(0, tamagotchi.money)
        
        # Добавляем действие в историю
        tamagotchi.actions_history.append(f"{now.strftime('%H:%M')}: {action.value}")
        if len(tamagotchi.actions_history) > 20:
            tamagotchi.actions_history.pop(0)
        
        self.save_data()
        return result
    
    def _get_final_result(self, tamagotchi: Tamagotchi) -> str:
        """Получить финальный результат в 13 лет"""
        score = (
            tamagotchi.intelligence * 0.3 +
            tamagotchi.money * 0.3 +
            tamagotchi.reputation * 0.2 +
            tamagotchi.health * 0.1 +
            tamagotchi.happiness * 0.1
        )
        
        if score > 2000:
            return ("\n🎊 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! 🎊\n"
                   f"{tamagotchi.name} вырос(ла) успешным человеком!\n"
                   f"Состояние: {tamagotchi.money} руб.\n"
                   "Будущее: бизнесмен/ученый/артист 💼")
        elif score > 1000:
            return ("\n👍 ХОРОШИЙ РЕЗУЛЬТАТ!\n"
                   f"{tamagotchi.name} живет обычной жизнью.\n"
                   f"Состояние: {tamagotchi.money} руб.")
        else:
            return ("\n⚠️ ПЛОХОЙ РЕЗУЛЬТАТ!\n"
                   f"{tamagotchi.name} попал(а) в тюрьму!\n"
                   "Причина: низкие интеллект и репутация ⛓️")
    
    def auto_sleep_check(self):
        """Автоматически проверяем, не пора ли спать"""
        now = datetime.now()
        for tamagotchi in self.tamagotchis.values():
            if not tamagotchi.is_sleeping:
                # Если поздно вечером (после 22:00) или бодрствует более 16 часов
                if now.hour >= 22 or (tamagotchi.wake_up_time and 
                                    (now - tamagotchi.wake_up_time).seconds > 57600):
                    tamagotchi.is_sleeping = True
                    tamagotchi.sleep_time = now
                    # Немного штрафуем за поздний отход ко сну
                    tamagotchi.health -= random.randint(5, 10)
                    logger.info(f"Auto-sleep for {tamagotchi.name}")
        self.save_data()
    
    def get_status(self, user_id: int) -> str:
        """Получить статус тамагочи"""
        tamagotchi = self.get_tamagotchi(user_id)
        if not tamagotchi:
            return "У вас нет тамагочи! Создайте его командой /start"
        
        # Полоски прогресса
        def progress_bar(value, max_value=100):
            filled = int(value / max_value * 10)
            return '█' * filled + '░' * (10 - filled)
        
        status = (
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
            status += f"📝 Последнее действие: {tamagotchi.last_action}\n"
        
        # Показываем последние 3 действия
        if tamagotchi.actions_history:
            status += "\n📜 Последние действия:\n"
            for action in tamagotchi.actions_history[-3:]:
                status += f"  • {action}\n"
        
        return status

class Tournament:
    def __init__(self):
        self.scores = defaultdict(int)
        self.load_tournament_data()
    
    def load_tournament_data(self):
        """Загрузить данные турнира"""
        try:
            if os.path.exists(TOURNAMENT_FILE):
                with open(TOURNAMENT_FILE, 'r', encoding='utf-8') as f:
                    self.scores = defaultdict(int, json.load(f))
        except Exception as e:
            logger.error(f"Error loading tournament data: {e}")
    
    def save_tournament_data(self):
        """Сохранить данные турнира"""
        try:
            with open(TOURNAMENT_FILE, 'w', encoding='utf-8') as f:
                json.dump(dict(self.scores), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving tournament data: {e}")
    
    def update_score(self, user_id: int, tamagotchi: Tamagotchi):
        """Обновить счет в турнире"""
        score = (
            tamagotchi.intelligence * 2 +
            tamagotchi.money // 5 +
            tamagotchi.reputation * 3 +
            tamagotchi.health +
            tamagotchi.happiness * 2
        )
        self.scores[user_id] = score
        self.save_tournament_data()
    
    def get_leaderboard(self, game: TamagotchiGame) -> str:
        """Получить турнирную таблицу"""
        if not self.scores:
            return "🏆 Турнирная таблица пуста! Создайте тамагочи и начните играть!"
        
        leaderboard = "🏆 ТУРНИРНАЯ ТАБЛИЦА 🏆\n\n"
        
        # Сортируем по очкам
        sorted_scores = sorted(
            self.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, (user_id, score) in enumerate(sorted_scores[:10]):
            tamagotchi = game.get_tamagotchi(user_id)
            if tamagotchi:
                medal = medals[i] if i < len(medals) else f"{i+1}."
                leaderboard += f"{medal} {tamagotchi.name}: {score} очков\n"
        
        return leaderboard

# Инициализация игры и турнира
game = TamagotchiGame()
tournament = Tournament()

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
        "Вырастите своего виртуального ребенка от рождения до 13 лет!\n"
        "Каждый день заботьтесь о нем, развивайте и следите за его успехами.\n\n"
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
    
    # Обновляем турнир
    tournament.update_score(user_id, tamagotchi)
    
    await update.message.reply_text(
        f"🎉 Поздравляем! Вы создали {gender.value} по имени {name}!\n\n"
        f"👶 {name} только что родился(ась) и ждет вашей заботы!\n\n"
        f"📋 Основные команды:\n"
        f"/status - состояние тамагочи\n"
        f"/actions - доступные действия\n"
        f"/wakeup - разбудить (если спит)\n"
        f"/sleep - уложить спать\n"
        f"/leaderboard - турнирная таблица\n"
        f"/help - подробная справка\n\n"
        f"Цель: вырастить успешного ребенка к 13 годам! 🎯"
    )
    
    del context.user_data['creating_gender']

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус тамагочи"""
    user_id = update.effective_user.id
    status_text = game.get_status(user_id)
    
    # Обновляем счет в турнире
    tamagotchi = game.get_tamagotchi(user_id)
    if tamagotchi:
        tournament.update_score(user_id, tamagotchi)
    
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
        await update.message.reply_text(
            f"{tamagotchi.name} спит! 💤\n"
            "Доступные действия:\n"
            "/wakeup - разбудить\n"
            "/status - посмотреть состояние"
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🚿 Умыться", callback_data="action_wash"),
            InlineKeyboardButton("🍳 Завтрак", callback_data="action_breakfast")
        ],
        [
            InlineKeyboardButton("💪 Зарядка", callback_data="action_exercise"),
            InlineKeyboardButton("🛏️ Заправить кровать", callback_data="action_make_bed")
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
            InlineKeyboardButton("🚿 Душ", callback_data="action_shower")
        ],
        [
            InlineKeyboardButton("🎮 Играть на ПК", callback_data="action_computer"),
            InlineKeyboardButton("🎨 Рисовать", callback_data="action_draw")
        ],
        [
            InlineKeyboardButton("🏡 В гости", callback_data="action_visit"),
            InlineKeyboardButton("🚶 Гулять", callback_data="action_walk")
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
            InlineKeyboardButton("🎉 Вечеринка", callback_data="action_party")
        ],
        [
            InlineKeyboardButton("🌙 Ночевка", callback_data="action_sleepover"),
            InlineKeyboardButton("🍪 Печь печенье", callback_data="action_bake")
        ],
        [
            InlineKeyboardButton("👊 Драться", callback_data="action_fight"),
            InlineKeyboardButton("❤️ Влюбиться", callback_data="action_love")
        ],
        [
            InlineKeyboardButton("📱 Вести блог", callback_data="action_blog"),
            InlineKeyboardButton("💬 Общаться", callback_data="action_chat")
        ],
        [
            InlineKeyboardButton("😴 Спать", callback_data="action_sleep")
        ]
    ]
    
    await update.message.reply_text(
        f"Выберите действие для {tamagotchi.name}:\n"
        "💡 Совет: чередуйте разные активности для лучшего развития!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action_name = query.data.replace("action_", "")
    
    try:
        action = Action[action_name.upper()]
        result = game.perform_action(user_id, action)
        
        # Обновляем счет в турнире
        tamagotchi = game.get_tamagotchi(user_id)
        if tamagotchi:
            tournament.update_score(user_id, tamagotchi)
        
        # Добавляем кнопку для новых действий
        keyboard = [[
            InlineKeyboardButton("📋 Еще действия", callback_data="more_actions"),
            InlineKeyboardButton("📊 Статус", callback_data="show_status")
        ]]
        
        await query.edit_message_text(
            f"{result}\n\n"
            f"Что дальше?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except KeyError:
        await query.edit_message_text("Неизвестное действие!")

async def more_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать еще действий"""
    query = update.callback_query
    await query.answer()
    await show_actions_callback(update, context)

async def show_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус через callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    status_text = game.get_status(user_id)
    
    # Добавляем кнопки действий
    keyboard = [[
        InlineKeyboardButton("📋 Действия", callback_data="more_actions"),
        InlineKeyboardButton("🏆 Лидерборд", callback_data="show_leaderboard")
    ]]
    
    await query.edit_message_text(
        status_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_actions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать действия через callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    tamagotchi = game.get_tamagotchi(user_id)
    
    if not tamagotchi:
        await query.edit_message_text("У вас нет тамагочи! Создайте его командой /start")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🚿 Умыться", callback_data="action_wash"),
            InlineKeyboardButton("🍳 Завтрак", callback_data="action_breakfast")
        ],
        [
            InlineKeyboardButton("💪 Зарядка", callback_data="action_exercise"),
            InlineKeyboardButton("🛏️ Заправить кровать", callback_data="action_make_bed")
        ],
        [
            InlineKeyboardButton("📚 Читать", callback_data="action_read"),
            InlineKeyboardButton("🏫 Школа", callback_data="action_school")
        ],
        [
            InlineKeyboardButton("📊 Статус", callback_data="show_status"),
            InlineKeyboardButton("🏆 Лидерборд", callback_data="show_leaderboard")
        ]
    ]
    
    await query.edit_message_text(
        f"Выберите действие для {tamagotchi.name}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать лидерборд через callback"""
    query = update.callback_query
    await query.answer()
    
    leaderboard_text = tournament.get_leaderboard(game)
    
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
    leaderboard_text = tournament.get_leaderboard(game)
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
        "Вырастить тамагочи от рождения до 13 лет.\n"
        "Чем лучше вы о нем заботитесь, тем успешнее он станет!\n\n"
        
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
        "1. Следите за сном тамагочи\n"
        "2. Балансируйте между работой и отдыхом\n"
        "3. Развивайте все характеристики\n"
        "4. Участвуйте в социальных активностях\n"
        "5. Избегайте драк и прогулов школы\n\n"
        
        "📞 ПОДДЕРЖКА:\n"
        "Бот работает автономно 24/7\n"
        "Данные сохраняются автоматически"
    )
    await update.message.reply_text(help_text)

async def auto_sleep_task(context: ContextTypes.DEFAULT_TYPE):
    """Автоматическая проверка сна"""
    try:
        game.auto_sleep_check()
        logger.info("Auto-sleep check completed")
    except Exception as e:
        logger.error(f"Error in auto_sleep_task: {e}")

async def post_leaderboard_to_channel(context: ContextTypes.DEFAULT_TYPE):
    """Размещение турнирной таблицы в канале"""
    try:
        if CHANNEL_ID:
            leaderboard_text = tournament.get_leaderboard(game)
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🏆 ЕЖЕДНЕВНАЯ ТУРНИРНАЯ ТАБЛИЦА 🏆\n\n{leaderboard_text}\n\nИграйте: @{context.bot.username}"
            )
            logger.info(f"Posted leaderboard to channel {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Error posting to channel: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка. Пожалуйста, попробуйте снова."
            )
    except:
        pass

async def setup_webhook(application: Application):
    """Настройка webhook для Render"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        await application.bot.set_webhook(
            url=webhook_url,
            max_connections=40,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set, using polling")

async def health_check(context: ContextTypes.DEFAULT_TYPE):
    """Проверка здоровья бота"""
    try:
        # Сохраняем данные
        game.save_data()
        tournament.save_tournament_data()
        logger.info("Health check completed - data saved")
    except Exception as e:
        logger.error(f"Health check error: {e}")

def main():
    """Основная функция запуска бота"""
    
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
    application.add_handler(CommandHandler("stats", status))  # Альтернатива для /status
    
    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(create_tamagotchi, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(handle_action, pattern="^action_"))
    application.add_handler(CallbackQueryHandler(more_actions, pattern="^more_actions$"))
    application.add_handler(CallbackQueryHandler(show_status_callback, pattern="^show_status$"))
    application.add_handler(CallbackQueryHandler(show_actions_callback, pattern="^show_actions$"))
    application.add_handler(CallbackQueryHandler(show_leaderboard_callback, pattern="^show_leaderboard$"))
    
    # Обработчик текстовых сообщений (для имени)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_name))
    
    if WEBHOOK_URL:
        # Запуск через webhook (для Render)
        logger.info("Starting bot with webhook...")
        
        async def start_webhook():
            await setup_webhook(application)
            
            # Настраиваем планировщик задач
            job_queue = application.job_queue
            if job_queue:
                # Проверка сна каждые 30 минут
                job_queue.run_repeating(auto_sleep_task, interval=1800, first=10)
                # Проверка здоровья каждые 5 минут
                job_queue.run_repeating(health_check, interval=300, first=5)
                # Постинг турнирной таблицы в канал каждые 24 часа
                job_queue.run_repeating(post_leaderboard_to_channel, interval=86400, first=60)
            
            # Запускаем приложение
            await application.initialize()
            await application.start()
            
            # Держим приложение запущенным
            await asyncio.Event().wait()
        
        # Запускаем веб-сервер для Render
        from aiohttp import web
        
        async def handle_webhook(request):
            """Обработчик webhook запросов"""
            if request.method == "POST":
                data = await request.json()
                update = Update.de_json(data, application.bot)
                await application.process_update(update)
                return web.Response(text="OK")
            return web.Response(text="Method not allowed", status=405)
        
        async def handle_health(request):
            """Health check endpoint для Render"""
            return web.Response(text="OK", status=200)
        
        async def start_server():
            """Запуск сервера"""
            app = web.Application()
            app.router.add_post(f'/{TOKEN}', handle_webhook)
            app.router.add_get('/health', handle_health)
            app.router.add_get('/', handle_health)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()
            
            logger.info(f"Server started on port {PORT}")
            
            # Запускаем бота
            await start_webhook()
        
        # Запускаем asyncio event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server())
        loop.run_forever()
        
    else:
        # Запуск через polling (для локальной разработки)
        logger.info("Starting bot with polling...")
        
        # Настраиваем планировщик задач
        job_queue = application.job_queue
        if job_queue:
            # Проверка сна каждые 30 минут
            job_queue.run_repeating(auto_sleep_task, interval=1800, first=10)
            # Проверка здоровья каждые 5 минут
            job_queue.run_repeating(health_check, interval=300, first=5)
            # Постинг турнирной таблицы в канал каждые 24 часа
            job_queue.run_repeating(post_leaderboard_to_channel, interval=86400, first=60)
        
        # Запуск polling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

if __name__ == '__main__':
    main()
