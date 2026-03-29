"""
Модуль машинного обучения (ML Service Layer).
Реализует алгоритмы обработки естественного языка (NLP) и кластеризации
для автоматической семантической группировки текстов.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from app.db.crud import get_all_posts, add_tag_to_post


def run_smart_clustering() -> dict:
    """
    Запускает конвейер (пайплайн) машинного обучения:
    1. Формирование корпуса текстов из базы данных.
    2. Векторизация и оценка важности терминов методом TF-IDF.
    3. Обучение модели неконтролируемой кластеризации (K-Means).
    4. Извлечение ключевых признаков (центроидов) и автоматическое тегирование.

    :return: Словарь со статусом выполнения и информационным сообщением.
    """
    posts = get_all_posts()

    # Защита от запуска при недостатке данных: для корректной работы
    # статистических алгоритмов требуется минимальный объем выборки.
    if len(posts) < 5:
        return {"status": "error", "message": "Недостаточно данных. Нужно минимум 5 сохраненных записей."}

    # 1. Подготовка корпуса данных (Dataset)
    corpus = []
    post_ids = []
    for p in posts:
        # Объединение категории (сабреддита) и заголовка для обогащения контекста модели
        text = f"{p.subreddit} {p.title}"
        corpus.append(text)
        post_ids.append(p.id)

    # 2. Векторизация (преобразование текста в математическую матрицу признаков).
    # stop_words='english' исключает из анализа шумовые слова (предлоги, союзы, артикли).
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    try:
        X = vectorizer.fit_transform(corpus)
    except ValueError:
        return {"status": "error", "message": "Ошибка векторизации. Тексты слишком короткие или пустые."}

    # 3. Кластеризация (Группировка по смыслу)
    # Динамический расчет оптимального числа кластеров в зависимости от объема выборки
    # (в среднем 1 тематическая группа на каждые 5 записей, в диапазоне от 2 до 10).
    num_clusters = max(2, min(len(posts) // 5, 10))

    # Инициализация и обучение алгоритма k-средних (K-Means)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(X)

    # 4. Извлечение центроидов (наиболее значимых слов для каждого кластера)
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()

    cluster_tags = {}
    for i in range(num_clusters):
        # Выбор двух терминов с наибольшим математическим весом для формирования названия категории
        top_words = [terms[ind] for ind in order_centroids[i, :2]]
        cluster_tags[i] = f"auto: {'-'.join(top_words)}"

    # 5. Автоматическое сохранение результатов классификации в базу данных
    labels = kmeans.labels_
    tags_added = 0
    for i, post_id in enumerate(post_ids):
        cluster_id = labels[i]
        tag_name = cluster_tags[cluster_id]

        # Делегирование операции привязки тега слою доступа к данным
        if add_tag_to_post(post_id, tag_name):
            tags_added += 1

    return {
        "status": "success",
        "message": f"Обучение завершено. Выделено кластеров: {num_clusters}. Присвоено авто-тегов: {tags_added}."
    }