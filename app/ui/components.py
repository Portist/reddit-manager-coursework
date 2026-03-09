"""
Модуль изолированных UI-компонентов (Presentation Layer).
Содержит функции рендеринга повторяющихся элементов интерфейса.
"""
import streamlit as st
from app.db.crud import add_tag_to_post, delete_post_from_db


def render_post_card(post) -> None:
    """
    Отрисовывает карточку отдельного поста с элементами управления
    (добавление тега, безвозвратное удаление).
    """
    current_tags = [t.name for t in post.tags]
    tags_str = ", ".join(current_tags) if current_tags else "Нет тегов"

    with st.expander(f"[{post.subreddit}] {post.title}"):
        st.markdown(f"**Источник:** [Перейти на Reddit]({post.url})")
        st.markdown(f"**Категории (Теги):** `{tags_str}`")

        # Разметка UI-сетки для выравнивания элементов управления
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            new_tag = st.text_input("Добавить тег:", key=f"input_{post.id}")

        with col2:
            st.write("")
            st.write("")
            if st.button("➕ Добавить", key=f"btn_add_{post.id}"):
                if new_tag:
                    if add_tag_to_post(post.id, new_tag):
                        st.rerun()

        with col4:
            st.write("")
            st.write("")
            if st.button("🗑️ Удалить", key=f"btn_del_{post.id}", type="primary"):
                if delete_post_from_db(post.id):
                    st.rerun()