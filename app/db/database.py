"""
Модуль инициализации соединения с базой данных.
Настраивает ядро (engine) SQLAlchemy и фабрику сессий для безопасного управления транзакциями.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Извлечение пути к файлу базы данных из строки подключения (убираем префикс 'sqlite:///')
db_path = settings.DATABASE_URL.replace("sqlite:///", "")

# Гарантированное создание директории для хранения файла базы данных.
# Если папка 'data' отсутствует, она будет создана автоматически.
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Инициализация основного движка SQLAlchemy.
# Параметр echo=False отключает вывод каждого SQL-запроса в консоль для чистоты вывода.
engine = create_engine(settings.DATABASE_URL, echo=False)

# Фабрика изолированных сессий (реализует паттерн проектирования "Единица работы" / Unit of Work).
# autocommit=False гарантирует, что разработчик должен явно подтверждать изменения,
# что защищает базу от частичной и некорректной записи данных.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)