"""
Модуль интеграционного слоя.
Отвечает за взаимодействие с внешним источником данных (платформой Reddit)
через механизм приватных лент в формате JSON.
Реализует управление сессиями, внедрение файлов Cookie и механизм обхода пагинации.
"""
import requests
import time
from app.core.config import settings

def fetch_saved_posts() -> list[dict]:
    """
    Выполняет агрегацию сохраненных записей пользователя из внешнего источника.
    Реализует алгоритм итеративного сбора данных (пагинации) для обхода ограничений на количество записей в одном ответе.

    :raises ValueError: В случае отсутствия конфигурационного параметра REDDIT_PRIVATE_FEED_URL.
    :return: Список нормализованных словарей с данными извлеченных публикаций.
    """
    if not settings.REDDIT_PRIVATE_FEED_URL:
        raise ValueError("CRITICAL: В переменных окружения не задан параметр REDDIT_PRIVATE_FEED_URL")

    # Формирование заголовков запроса для имитации легитимного клиента
    headers = {"User-Agent": settings.USER_AGENT}
    cookies = {}
    if hasattr(settings, 'REDDIT_SESSION_COOKIE') and settings.REDDIT_SESSION_COOKIE:
        cookies['reddit_session'] = settings.REDDIT_SESSION_COOKIE

    print("INFO: Инициализация HTTP-запроса к приватному шлюзу Reddit...")

    posts = []

    # Маркер для запроса следующей страницы данных
    after = None

    # Формирование базового URL с максимальным лимитом элементов на страницу
    base_url = settings.REDDIT_PRIVATE_FEED_URL
    if "?" in base_url:
        base_url += "&limit=100"
    else:
        base_url += "?limit=100"

    while True:
        current_url = base_url
        if after:
            current_url += f"&after={after}"
            print(f"INFO: Запрос следующей страницы (after={after})...")

        response = requests.get(current_url, headers=headers, cookies=cookies)

        if response.status_code == 200:
            data = response.json()
            children = data.get('data', {}).get('children', [])

            if not children:
                break

            for item in children:
                post_data = item.get('data', {})

                # Фильтрация по типу контента 't3' (обозначение стандартных публикаций в API Reddit)
                if item.get('kind') == 't3':

                    media_urls = []
                    url = post_data.get("url", "")
                    thumbnail = post_data.get("thumbnail", "")

                    # Извлечение высококачественных изображений из структуры типа 'Галерея'
                    if post_data.get("is_gallery") and "media_metadata" in post_data:
                        metadata = post_data["media_metadata"]
                        for gallery_item in post_data.get("gallery_data", {}).get("items", []):
                            media_id = gallery_item.get("media_id")
                            if media_id and media_id in metadata:
                                raw_url = metadata[media_id].get("s", {}).get("u", "")
                                if raw_url:
                                    media_urls.append(raw_url.replace("&amp;", "&"))

                    # Обработка одиночных прямых ссылок на графические файлы
                    elif url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        media_urls.append(url)

                    # Извлечение адреса видеопотока
                    elif post_data.get("is_video"):
                        vid_url = post_data.get("media", {}).get("reddit_video", {}).get("fallback_url")
                        if vid_url: media_urls.append(vid_url)

                    # Извлечение изображения предварительного просмотра (превью)
                    elif "preview" in post_data and "images" in post_data["preview"]:
                        raw_url = post_data["preview"]["images"][0]["source"]["url"]
                        media_urls.append(raw_url.replace("&amp;", "&"))

                    # Использование стандартной миниатюры в качестве резервного варианта
                    elif thumbnail and thumbnail.startswith("http"):
                        media_urls.append(thumbnail)

                    # Объединение списка ссылок в единую строку для хранения в реляционной БД
                    media_url_str = "|".join(media_urls) if media_urls else None

                    # Извлечение текстового содержимого с удалением начальных и конечных пробелов
                    selftext = post_data.get("selftext", "").strip()
                    selftext = selftext if selftext else None

                    # Формирование стандартизированного словаря для передачи на уровень доступа к данным
                    posts.append({
                        "id": post_data.get("name"),
                        "title": post_data.get("title"),
                        "url": post_data.get("url"),
                        "subreddit": post_data.get("subreddit_name_prefixed"),
                        "media_url": media_url_str,
                        "selftext": selftext
                    })

            # Обновление маркера пагинации
            after = data.get('data', {}).get('after')
            if not after:
                break

            # Задержка выполнения для предотвращения блокировки со стороны сервера по лимиту запросов
            time.sleep(1)

        else:
            print(f"ERROR: Ошибка HTTP-запроса: Код {response.status_code}")
            break

    print(f"INFO: Десериализация завершена. Извлечено валидных записей: {len(posts)}")
    return posts