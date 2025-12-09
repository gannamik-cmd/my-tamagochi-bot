import os
from dotenv import load_dotenv

load_dotenv()

# Токен вашего бота (получите у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список администраторов (ваши ID в Telegram)
ADMIN_IDS = [123456789]  # Замените на свой ID

# Состояние бота: True - активен, False - спит
BOT_ACTIVE = True