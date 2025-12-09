"""
Простой файл для запуска бота на Render
"""
import os
import asyncio
from aiohttp import web
from bot import main

if name == 'main':
    # Проверяем переменные окружения
    if 'RENDER' in os.environ:
        # На Render используем asyncio.run
        asyncio.run(main())
    else:
        # Локально запускаем напрямую
        main()