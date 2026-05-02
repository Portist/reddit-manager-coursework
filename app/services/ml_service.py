"""
Модуль сервиса машинного обучения.
Реализует многоуровневый алгоритм кластеризации текстов.
Использует иерархический подход: первичная группировка по источникам данных
с последующим семантическим анализом внутри крупных кластеров с помощью алгоритма K-Means.
"""
import re
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.cluster import KMeans
from app.db.crud import get_all_posts, add_tag_to_post, delete_tags_bulk

# Расширенный словарь стоп-слов, объединяющий базовую лексику английского языка
# и специфический сленг платформы Reddit для повышения релевантности выделяемых признаков.
CUSTOM_STOP_WORDS = list(ENGLISH_STOP_WORDS) + [
    "don", "know", "like", "just", "people", "time", "good", "way",
    "really", "think", "make", "ve", "ll", "did", "does", "https",
    "com", "www", "reddit", "comments", "deleted", "removed", "amp",
    "want", "need", "use", "using", "work", "got", "help"
]

def run_smart_clustering() -> dict:
    """
    Запускает конвейер автоматической категоризации публикаций.
    Осуществляет векторизацию текстов и распределение записей по смысловым кластерам.

    :return: Словарь со статусом выполнения и статистикой обработки.
    """
    posts = get_all_posts()

    if len(posts) < 5:
        return {"status": "error", "message": "Недостаточно данных. Требуется минимум 5 сохраненных записей."}

    # Удаление устаревших автоматически сгенерированных категорий перед новым запуском
    deleted_old_tags = delete_tags_bulk(auto_only=True)

    # Первичная кластеризация: группировка публикаций по исходному сообществу
    sub_groups = defaultdict(list)
    for p in posts:
        clean_sub = p.subreddit.lower().replace("r/", "") if p.subreddit else "unknown"
        sub_groups[clean_sub].append(p)

    tags_added = 0
    clusters_formed = 0

    # Семантический анализ внутри каждой сформированной группы
    for sub_name, sub_posts in sub_groups.items():

        # Применение обобщенной категории при недостаточном объеме обучающей выборки
        if len(sub_posts) < 4:
            tag_name = f"auto: {sub_name}"
            for p in sub_posts:
                if add_tag_to_post(p.id, tag_name):
                    tags_added += 1
            clusters_formed += 1
            continue

        # Формирование текстового корпуса для применения алгоритмов машинного обучения
        corpus = []
        for p in sub_posts:
            raw_text = p.title
            if p.selftext:
                raw_text += " " + p.selftext

            # Нормализация текста: удаление специальных символов с сохранением букв и цифр
            clean_text = re.sub(r'[^a-zA-Zа-яА-Я0-9]+', ' ', raw_text)
            corpus.append(clean_text)

        # Инициализация векторизатора на основе метрики TF-IDF с учетом биграмм
        vectorizer = TfidfVectorizer(stop_words=CUSTOM_STOP_WORDS, ngram_range=(1, 2), max_features=500)

        try:
            X = vectorizer.fit_transform(corpus)
        except ValueError:
            # Обработка исключений, возникающих при пустом признаковом пространстве
            tag_name = f"auto: {sub_name}"
            for p in sub_posts:
                if add_tag_to_post(p.id, tag_name): tags_added += 1
            clusters_formed += 1
            continue

        # Динамическое вычисление оптимального количества кластеров
        num_clusters = max(2, int((len(sub_posts) / 2) ** 0.5))
        num_clusters = min(num_clusters, len(sub_posts))

        # Выполнение кластеризации методом K-Means
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(X)

        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        labels = kmeans.labels_

        # Извлечение значимых признаков и формирование иерархических категорий
        for i, p in enumerate(sub_posts):
            cluster_id = labels[i]

            # Определение наиболее релевантного словосочетания для текущего кластера
            top_phrase = terms[order_centroids[cluster_id, 0]]
            tag_name = f"auto: {sub_name} - {top_phrase}"

            if add_tag_to_post(p.id, tag_name):
                tags_added += 1

        clusters_formed += num_clusters

    return {
        "status": "success",
        "message": f"Готово! Очищено старых: {deleted_old_tags}. Сформировано смарт-категорий: {clusters_formed}. Назначено тегов: {tags_added}."
    }