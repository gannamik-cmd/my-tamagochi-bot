Николь, [09.12.2025 18:22]
services:
  - type: web
    name: tamagotchi-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: CHANNEL_ID
        sync: false
      - key: WEBHOOK_URL
        fromService:
          type: web
          name: tamagotchi-bot
          property: url
    healthCheckPath: /health

Николь, [09.12.2025 18:25]
import multiprocessing

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "aiohttp.GunicornWebWorker"
timeout = 120
keepalive = 5