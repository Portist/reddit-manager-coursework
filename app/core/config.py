"""
Модуль конфигурации приложения.
Загружает переменные окружения и устанавливает глобальные параметры системы.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    REDDIT_PRIVATE_FEED_URL = os.getenv("REDDIT_PRIVATE_FEED_URL")

    # Имитация браузерного заголовка для предотвращения блокировки (HTTP 429) со стороны Reddit
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    DATABASE_URL = "sqlite:///data/reddit_manager.db"


settings = Config()