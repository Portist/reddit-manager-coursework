"""
Модуль оркестрации (Service Layer).
Управляет процессом извлечения, преобразования и загрузки данных (ETL-процесс).
Выступает посредником между интеграционным клиентом и слоем доступа к данным.
"""
from app.services.reddit_client import fetch_saved_posts
from app.db.crud import save_reddit_posts_to_db


def run_sync_pipeline() -> int:
    """
    Запускает полный цикл синхронизации данных.

    :return: Количество новых успешно сохраненных записей в локальной базе данных.
    """
    # 1. Извлечение данных из внешнего источника
    fetched_data = fetch_saved_posts()
    if not fetched_data:
        return 0

    # 2. Загрузка нормализованных данных в локальное хранилище
    added_count = save_reddit_posts_to_db(fetched_data)
    return added_count