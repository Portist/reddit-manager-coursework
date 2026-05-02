"""
Модуль оркестрации интеграционных процессов.
Управляет жизненным циклом извлечения, преобразования и загрузки данных.
Выступает связующим звеном между сетевым клиентом и уровнем доступа к данным.
"""
from app.services.reddit_client import fetch_saved_posts
from app.db.crud import save_reddit_posts_to_db


def run_sync_pipeline() -> int:
    """
    Инициализирует и контролирует полный цикл синхронизации данных
    между внешним источником и локальным хранилищем.

    :return: Количество успешно добавленных уникальных записей в базу данных.
    """
    # Получение массива публикаций через клиент внешнего программного интерфейса
    fetched_data = fetch_saved_posts()
    if not fetched_data:
        return 0

    # Передача нормализованного массива данных на уровень сохранения
    added_count = save_reddit_posts_to_db(fetched_data)
    return added_count