"""
Модуль изолированных компонентов пользовательского интерфейса (Presentation Layer).
Содержит функции для отрисовки повторяющихся графических элементов.
"""
import streamlit as st
from app.db.crud import add_tag_to_post, delete_post_from_db, restore_post_in_db


def render_post_card(post, is_trash_mode: bool = False) -> None:
    """
    Отрисовывает интерактивную карточку отдельной записи с элементами управления.
    Адаптирует выводимые кнопки в зависимости от текущего режима работы (основной список или корзина).

    :param post: Объект записи из базы данных.
    :param is_trash_mode: Флаг отображения интерфейса корзины.
    """
    # Подготовка списка категорий для вывода
    current_tags = [t.name for t in post.tags]
    tags_str = ", ".join(current_tags) if current_tags else "Нет тегов"

    # Использование компонента "Аккордеон" для компактного отображения
    with st.expander(f"[{post.subreddit}] {post.title}"):

        # Динамическая замена домена: перенаправление с устаревшего интерфейса (old.reddit)
        # на современную версию платформы для улучшения пользовательского опыта (UX).
        clean_url = post.url.replace("old.reddit.com", "www.reddit.com") if post.url else "#"

        st.markdown(f"**Источник:** [Перейти на Reddit]({clean_url})")
        st.markdown(f"**Категории (Теги):** `{tags_str}`")

        # Разметка структурной сетки для выравнивания элементов управления
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        # Маршрутизация элементов управления: Режим корзины
        if is_trash_mode:
            with col4:
                # Атрибут key необходим для изоляции состояния одинаковых кнопок в цикле
                if st.button("Восстановить", key=f"btn_res_{post.id}", type="primary"):
                    if restore_post_in_db(post.id):
                        st.rerun() # Принудительное обновление интерфейса

        # Маршрутизация элементов управления: Основной режим работы
        else:
            with col1:
                new_tag = st.text_input("Добавить тег:", key=f"input_{post.id}")

            with col2:
                # Визуальные отступы для выравнивания кнопки относительно поля ввода
                st.write("")
                st.write("")
                if st.button("Добавить", key=f"btn_add_{post.id}"):
                    if new_tag:
                        if add_tag_to_post(post.id, new_tag):
                            st.rerun()

            with col4:
                st.write("")
                st.write("")
                # Выделение деструктивного действия акцентным цветом (type="primary")
                if st.button("Удалить", key=f"btn_del_{post.id}", type="primary"):
                    if delete_post_from_db(post.id):
                        st.rerun()