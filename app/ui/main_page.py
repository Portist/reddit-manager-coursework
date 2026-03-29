"""
Модуль слоя представления (Presentation Layer).
Реализует пользовательский веб-интерфейс на базе фреймворка Streamlit.
Отвечает за маршрутизацию действий пользователя к слою бизнес-логики.
"""
import streamlit as st
from app.db.crud import get_all_posts, get_all_tags, search_posts_by_title, get_deleted_posts
from app.services.sync_service import run_sync_pipeline
from app.ui.components import render_post_card
from app.services.ml_service import run_smart_clustering


def render_page() -> None:
    """
    Инициализирует глобальные параметры страницы и отрисовывает основные
    структурные блоки информационной панели (дашборда).
    """
    # Настройка метаданных веб-страницы
    st.set_page_config(page_title="Reddit Manager", page_icon="📚", layout="wide")
    st.title("Менеджер сохраненных записей Reddit")

    # Боковая панель: Элементы управления системными процессами
    st.sidebar.header("Управление системой")

    # Инициализация процесса синхронизации данных (ETL)
    if st.sidebar.button("Синхронизировать данные", use_container_width=True):
        with st.spinner("Извлечение данных через шлюз интеграции..."):
            added = run_sync_pipeline()
            st.sidebar.success(f"Синхронизация завершена. Новых записей добавлено: {added}")
            st.rerun()

    # Переключатель логического отображения (Основной список / Корзина)
    is_trash_mode = st.sidebar.toggle("Показать корзину")

    st.sidebar.markdown("---")

    # Инициализация модуля алгоритмического анализа текстов
    st.sidebar.header("ИИ Кластеризация")

    if st.sidebar.button("Запустить автоматическую группировку", use_container_width=True):
        with st.spinner("Векторизация текстов и поиск семантических кластеров (TF-IDF & K-Means)..."):
            result = run_smart_clustering()
            if result["status"] == "success":
                st.sidebar.success(result["message"])
            else:
                st.sidebar.warning(result["message"])
            st.rerun()

    st.sidebar.markdown("---")

    # Боковая панель: Инструменты поиска и фильтрации
    st.sidebar.header("Поиск и Фильтры")

    # Поле полнотекстового поиска
    search_query = st.sidebar.text_input("Поиск по ключевым словам в заголовке:")

    # Динамическое формирование списка доступных категорий
    all_tags = [t.name for t in get_all_tags()]
    selected_tags = st.sidebar.multiselect("Множественный фильтр по категориям:", all_tags)

    # Слой логики представления данных

    # Ветвление: Обработка режима корзины
    if is_trash_mode:
        st.info("Вы находитесь в режиме корзины. Здесь отображаются удалённые посты.")
        posts = get_deleted_posts()

    # Ветвление: Обработка режима полнотекстового поиска (делегируется СУБД)
    else:
        if search_query:
            posts = search_posts_by_title(search_query)
        else:
            posts = get_all_posts()

    # Обработка пустых состояний
    if not posts and not is_trash_mode:
        st.warning("Локальная база данных пуста. Выполните первичную синхронизацию.")
        return
    elif not posts and is_trash_mode:
        st.success("Корзина пуста.")
        return

    # Реализация механизма фильтрации в оперативной памяти (In-Memory Filtering).
    # Используется для снижения нагрузки на реляционную базу данных при сложных выборках
    # со связями типа "Многие-ко-многим".
    if selected_tags and not is_trash_mode:
        filtered_posts = []
        for p in posts:
            post_tag_names = [t.name for t in p.tags]
            if any(tag in post_tag_names for tag in selected_tags):
                filtered_posts.append(p)
        posts = filtered_posts

    # Вывод статистической информации
    st.subheader(f"Отображено записей: {len(posts)}")

    # Итеративная отрисовка графических компонентов с передачей состояния
    for p in posts:
        # Передаем флаг состояния в компонент карточки
        render_post_card(p, is_trash_mode=is_trash_mode)