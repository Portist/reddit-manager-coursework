"""
Модуль инициализации соединения с базой данных.
Настраивает ядро объектно-реляционного отображения и фабрику сессий
для безопасного и эффективного управления транзакциями.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Формирование относительного пути к файлу базы данных
db_path = settings.DATABASE_URL.replace("sqlite:///", "")

# Автоматическое создание целевой директории хранения при ее отсутствии
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Инициализация ядра SQLAlchemy с отключенным логированием запросов
engine = create_engine(settings.DATABASE_URL, echo=False)

# Создание фабрики изолированных сессий
# Параметр autocommit=False требует явного вызова commit() для сохранения изменений
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)