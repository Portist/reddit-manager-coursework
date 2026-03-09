"""
Модуль слоя представления (Presentation Layer).
Реализует пользовательский веб-интерфейс на базе фреймворка Streamlit.
Отвечает за маршрутизацию действий пользователя к слою бизнес-логики.
"""
import streamlit as st
from app.db.crud import get_all_posts, get_all_tags, search_posts_by_title
from app.services.sync_service import run_sync_pipeline
from app.ui.components import render_post_card


def render_page() -> None:
    """
    Инициализирует и отрисовывает компоненты дашборда.
    """
    st.set_page_config(page_title="Reddit Manager", page_icon="📚", layout="wide")
    st.title("📚 Менеджер сохраненных записей Reddit")

    # Инициализация панели управления (Sidebar)
    st.sidebar.header("⚙️ Управление")

    if st.sidebar.button("🔄 Синхронизировать", use_container_width=True):
        with st.spinner("Агрегация данных через шлюз..."):
            added = run_sync_pipeline()
            st.sidebar.success(f"Синхронизация завершена. Новых записей: {added}")
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Поиск и Фильтры")

    search_query = st.sidebar.text_input("Полнотекстовый поиск (по заголовку):")

    all_tags = [t.name for t in get_all_tags()]
    selected_tags = st.sidebar.multiselect("Фильтр по тегам (множественный выбор):", all_tags)

    # Выборка данных
    if search_query:
        posts = search_posts_by_title(search_query)
    else:
        posts = get_all_posts()

    if not posts and not search_query:
        st.warning("Локальная база данных пуста. Выполните первичную синхронизацию.")
        return
    elif not posts and search_query:
        st.info("По заданным критериям ничего не найдено.")
        return

    # In-memory фильтрация по тегам
    if selected_tags:
        filtered_posts = []
        for p in posts:
            post_tag_names = [t.name for t in p.tags]
            if any(tag in post_tag_names for tag in selected_tags):
                filtered_posts.append(p)
        posts = filtered_posts

    st.subheader(f"Отображено записей: {len(posts)}")

    # Делегирование рендеринга изолированному компоненту
    for p in posts:
        render_post_card(p)