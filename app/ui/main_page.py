"""
Модуль слоя представления.
Реализует пользовательский веб-интерфейс на базе фреймворка Streamlit.
Осуществляет маршрутизацию действий пользователя к слоям бизнес-логики и интеграции.
"""
import streamlit as st
from app.db.crud import (
    get_all_posts, get_all_tags, get_deleted_posts,
    delete_tags_bulk, get_posts_by_status, mark_posts_as_read_bulk,
    get_starred_posts, mark_posts_as_starred_bulk, delete_posts_bulk, restore_posts_bulk,
    search_posts_advanced
)
from app.services.sync_service import run_sync_pipeline
from app.ui.components import render_post_card
from app.services.ml_service import run_smart_clustering

def render_page() -> None:
    """
    Инициализирует и отрисовывает главный графический интерфейс приложения.
    Обрабатывает пользовательский ввод, управляет маршрутизацией и обновлением состояний.
    """
    # Первичная настройка параметров веб-страницы
    st.set_page_config(page_title="Reddit Manager", page_icon="📚", layout="wide")
    st.title("Менеджер сохраненных записей Reddit")

    # Блок навигации в боковой панели
    st.sidebar.header("Навигация")
    view_mode = st.sidebar.radio(
        "Раздел:",
        ["Новое", "Прочитанные", "Помеченные", "Корзина"],
        index=0
    )
    st.sidebar.markdown("---")

    # Инициализация процесса синхронизации данных с внешним источником
    if st.sidebar.button("Синхронизировать данные", use_container_width=True):
        with st.spinner("Извлечение данных через шлюз интеграции..."):
            added = run_sync_pipeline()
            st.sidebar.success(f"Синхронизация завершена. Добавлено: {added}")
            st.rerun()

    st.sidebar.markdown("---")

    # Блок управления поиском и фильтрацией
    st.sidebar.header("Умный поиск и Фильтры")

    search_query = st.sidebar.text_input("Поисковый запрос:", placeholder="Например: Python или tutorial")

    # Выбор атрибутов базы данных для выполнения расширенного поиска
    search_areas = st.sidebar.multiselect(
        "Где искать:",
        options=["Заголовки", "Сабреддиты", "Ссылки"],
        default=["Заголовки", "Сабреддиты"],
        help="Выберите поля базы данных, в которых будет производиться поиск совпадений."
    )

    # Загрузка и отображение доступных категорий для фильтрации
    all_tags = [t.name for t in get_all_tags()]
    selected_tags = st.sidebar.multiselect("Фильтр по категориям (тегам):", all_tags)

    st.sidebar.markdown("---")

    # Блок управления алгоритмами классификации и администрирования
    st.sidebar.header("ИИ и Управление")

    if st.sidebar.button("Запустить ИИ-группировку", use_container_width=True):
        with st.spinner("Векторизация текстов и поиск кластеров..."):
            result = run_smart_clustering()
            if result["status"] == "success": st.sidebar.success(result["message"])
            else: st.sidebar.warning(result["message"])
            st.rerun()

    with st.sidebar.expander("Очистка базы категорий"):
        if st.button("Удалить авто-теги (auto:)", use_container_width=True):
            with st.spinner("Удаление..."):
                deleted = delete_tags_bulk(auto_only=True)
                st.success(f"Удалено авто-тегов: {deleted}")
                st.rerun()
        st.write("")
        if st.button("Удалить все теги", use_container_width=True, type="primary"):
            with st.spinner("Полная очистка..."):
                deleted = delete_tags_bulk(auto_only=False)
                st.success(f"Удалено тегов: {deleted}")
                st.rerun()


    # Блок маршрутизации и применения бизнес-логики
    posts = []
    is_trash_mode = False

    # Извлечение данных на основе выбранного навигационного раздела
    if "Новое" in view_mode:
        posts = get_posts_by_status(is_read=False, is_deleted=False)
    elif "Прочитанные" in view_mode:
        posts = get_posts_by_status(is_read=True, is_deleted=False)
    elif "Помеченные" in view_mode:
        posts = get_starred_posts()
    elif "Корзина" in view_mode:
        posts = get_deleted_posts()
        is_trash_mode = True

    # Применение расширенного поиска к текущей выборке
    if search_query and not is_trash_mode:
        search_results = search_posts_advanced(search_query, search_areas)

        # Использование структуры множества для обеспечения константного времени поиска O(1)
        valid_ids = {p.id for p in search_results}

        # Вычисление пересечения текущей выборки с результатами поиска
        posts = [p for p in posts if p.id in valid_ids]

    # Фильтрация данных в оперативной памяти на основе выбранных категорий
    if selected_tags and not is_trash_mode:
        posts = [p for p in posts if any(t.name in selected_tags for t in p.tags)]

    # Блок рендеринга динамического интерфейса

    # Вычисление массива идентификаторов публикаций, выделенных пользователем
    selected_ids = [p.id for p in posts if st.session_state.get(f"chk_{p.id}", False)]

    # Отображение панели групповых операций при наличии выделенных элементов
    if selected_ids:
        st.info(f"**Выбрано записей: {len(selected_ids)}**")
        if not is_trash_mode:
            c1, c2, c3, c4, c5 = st.columns(5)
            if c1.button("Прочитано", use_container_width=True):
                mark_posts_as_read_bulk(selected_ids, True)
                st.rerun()
            if c2.button("В Новое", use_container_width=True):
                mark_posts_as_read_bulk(selected_ids, False)
                st.rerun()
            if c3.button("Пометить", use_container_width=True):
                mark_posts_as_starred_bulk(selected_ids, True)
                st.rerun()
            if c4.button("Снять метку", use_container_width=True):
                mark_posts_as_starred_bulk(selected_ids, False)
                st.rerun()
            if c5.button("Удалить", use_container_width=True, type="primary"):
                delete_posts_bulk(selected_ids)
                st.rerun()
        else:
            if st.button("Восстановить выбранные", type="primary"):
                restore_posts_bulk(selected_ids)
                st.rerun()

    # Рендеринг итогового списка публикаций
    st.subheader(f"Отображено записей: {len(posts)}")

    if not posts:
        st.markdown("*Здесь пока пусто или по вашему запросу ничего не найдено...*")

    for post in posts:
        render_post_card(post, is_trash_mode=is_trash_mode)