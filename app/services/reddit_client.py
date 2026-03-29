"""
Модуль интеграционного слоя (Service Layer).
Отвечает за взаимодействие с внешним источником данных (платформой Reddit)
через легитимный механизм приватных лент (JSON-шлюз).
Реализует внедрение сессионных файлов (Cookie) для обхода сетевых политик платформы.
"""
import requests
from app.core.config import settings


def fetch_saved_posts() -> list[dict]:
    """
    Выполняет агрегацию сохраненных записей пользователя.
    Реализует десериализацию и нормализацию (преобразование форматов)
    входящей структуры данных для последующей передачи слою бизнес-логики.

    :return: Список нормализованных словарей с метаданными записей.
    :raises ValueError: В случае отсутствия конфигурационного URL-адреса.
    """
    if not settings.REDDIT_PRIVATE_FEED_URL:
        raise ValueError("CRITICAL: В переменных окружения не задан параметр REDDIT_PRIVATE_FEED_URL")

    # Использование пользовательского заголовка для маскировки под стандартный веб-браузер
    headers = {"User-Agent": settings.USER_AGENT}

    # Подготовка словаря с идентификаторами сессии для подтверждения авторизации пользователя
    cookies = {}
    if hasattr(settings, 'REDDIT_SESSION_COOKIE') and settings.REDDIT_SESSION_COOKIE:
        cookies['reddit_session'] = settings.REDDIT_SESSION_COOKIE

    print("INFO: Инициализация HTTP-запроса к приватному шлюзу Reddit...")

    # Отправка сетевого запроса с передачей заголовков и параметров сессии
    response = requests.get(
        settings.REDDIT_PRIVATE_FEED_URL,
        headers=headers,
        cookies=cookies
    )

    if response.status_code == 200:
        data = response.json()
        posts = []

        # Безопасное извлечение вложенных структур из ответа сервера
        children = data.get('data', {}).get('children', [])
        for item in children:
            post_data = item.get('data', {})

            # Фильтрация объектов: системный префикс 't3' строго соответствует
            # типу сущности "Запись" (Text/Link Post). Комментарии игнорируются.
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
        if response.status_code == 403:
            print("INFO: Возможно, сессионный Cookie истек или скопирован неверно.")
        return []