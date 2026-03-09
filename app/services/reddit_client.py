"""
Модуль интеграционного слоя (Service Layer).
Отвечает за взаимодействие с внешним источником данных (платформа Reddit)
через легитимный механизм приватных RSS/JSON лент.
"""
import requests
from app.core.config import settings


def fetch_saved_posts() -> list[dict]:
    """
    Выполняет агрегацию сохраненных записей пользователя через приватный JSON-шлюз.
    Реализует десериализацию и нормализацию (Data Mapping) входящей структуры данных
    для последующей передачи на слой доступа к данным (DAL).

    :return: Список нормализованных словарей с метаданными постов.
    :raises ValueError: В случае отсутствия конфигурационного URL-адреса.
    """
    if not settings.REDDIT_PRIVATE_FEED_URL:
        raise ValueError("CRITICAL: В переменных окружения не задан параметр REDDIT_PRIVATE_FEED_URL")

    # Передача кастомного заголовка User-Agent необходима для прохождения
    # базовых антибот-фильтров (WAF) на стороне сервера платформы
    headers = {"User-Agent": settings.USER_AGENT}

    print("INFO: Инициализация HTTP-запроса к приватному шлюзу Reddit...")
    response = requests.get(settings.REDDIT_PRIVATE_FEED_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        posts = []

        # Безопасное извлечение вложенных структур JSON
        children = data.get('data', {}).get('children', [])
        for item in children:
            post_data = item.get('data', {})

            # Фильтрация объектов: префикс 't3' в API Reddit жестко соответствует
            # типу сущности "Пост" (Link/Text Post). Комментарии ('t1') игнорируются.
            if item.get('kind') == 't3':
                posts.append({
                    "id": post_data.get("name"),
                    "title": post_data.get("title"),
                    "url": post_data.get("url"),
                    "subreddit": post_data.get("subreddit_name_prefixed")
                })

        print(f"INFO: Десериализация завершена. Извлечено валидных записей: {len(posts)}")
        return posts

    else:
        print(f"ERROR: Ошибка интеграционного шлюза. HTTP Status: {response.status_code}")
        return []