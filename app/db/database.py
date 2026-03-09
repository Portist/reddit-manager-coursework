"""
Модуль инициализации соединения с базой данных.
Настраивает SQLAlchemy engine и фабрику сессий для управления транзакциями.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Извлечение относительного пути для инициализации файловой системы
db_path = settings.DATABASE_URL.replace("sqlite:///", "")

# Гарантируем наличие директории для слоя персистентности перед созданием engine
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Инициализация ядра SQLAlchemy (SQL logging отключен для оптимизации консоли)
engine = create_engine(settings.DATABASE_URL, echo=False)

# Фабрика изолированных сессий (реализация паттерна Unit of Work)
# autocommit=False гарантирует явное управление транзакциями (commit/rollback на уровне сервисов)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)