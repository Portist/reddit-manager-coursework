"""
Модуль оркестрации (Service Layer).
Управляет пайплайном синхронизации данных: извлечение из внешнего API и загрузка в БД (ETL).
Подготовлен для внедрения промежуточного шага трансформации (NLP/Кластеризация).
"""
from app.services.reddit_client import fetch_saved_posts
from app.db.crud import save_reddit_posts_to_db


def run_sync_pipeline() -> int:
    """
    Запускает полный цикл агрегации данных.

    :return: Количество новых успешно сохраненных записей.
    """
    fetched_data = fetch_saved_posts()
    if not fetched_data:
        return 0

    # Место для будущего расширения (NLP, векторизация текста, TF-IDF)
    # enriched_data = process_text_data(fetched_data)

    added_count = save_reddit_posts_to_db(fetched_data)
    return added_count