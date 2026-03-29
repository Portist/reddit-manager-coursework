"""
Модуль изолированных компонентов пользовательского интерфейса.
Содержит функции для отрисовки повторяющихся графических элементов.
"""
import streamlit as st
from app.db.crud import add_tag_to_post, delete_post_from_db, restore_post_in_db, remove_tag_from_post


def render_post_card(post, is_trash_mode: bool = False) -> None:
    """
    Отрисовывает интерактивную карточку отдельной записи с элементами управления.
    Адаптирует выводимые кнопки в зависимости от текущего режима работы (основной список или корзина).

    :param post: Объект записи из базы данных.
    :param is_trash_mode: Флаг отображения интерфейса корзины.
    """
    # Подготовка списка категорий для вывода
    current_tags = [t.name for t in post.tags]
    tags_str = ", ".join(current_tags) if current_tags else "Нет категорий"

    # Использование компонента "Аккордеон" для компактного отображения
    with st.expander(f"[{post.subreddit}] {post.title}"):

        # Динамическая замена домена: перенаправление с устаревшего интерфейса (old.reddit)
        # на современную версию платформы для улучшения пользовательского опыта (UX).
        clean_url = post.url.replace("old.reddit.com", "www.reddit.com") if post.url else "#"

        st.markdown(f"**Источник:** [Перейти на Reddit]({clean_url})")
        st.markdown(f"**Теги:** `{tags_str}`")

        # Маршрутизация элементов управления: Режим корзины
        if is_trash_mode:
            col_res1, col_res2 = st.columns([8, 2])
            with col_res2:
                # Атрибут key необходим для изоляции состояния одинаковых кнопок в цикле
                if st.button("Восстановить", key=f"btn_res_{post.id}", type="primary"):
                    if restore_post_in_db(post.id):
                        st.rerun() # Принудительное обновление интерфейса

        # Маршрутизация элементов управления: Основной режим работы
        else:
            st.markdown("---")

            # Секция управления категориями (тегами)
            col1, col2, col3, col4 = st.columns([3, 2, 3, 2])

            with col1:
                new_tag = st.text_input("Добавить:", key=f"input_{post.id}")
            with col2:
                st.write("")
                st.write("")
                if st.button("Добавить", key=f"btn_add_{post.id}"):
                    if new_tag and add_tag_to_post(post.id, new_tag):
                        st.rerun()

            with col3:
                # Если теги есть - показываем выпадающий список. Если нет - блокируем его.
                if current_tags:
                    tag_to_remove = st.selectbox("Удалить:", current_tags, key=f"sel_rm_{post.id}")
                else:
                    st.selectbox("Удалить:", ["Нет"], disabled=True, key=f"sel_rm_{post.id}")
                    tag_to_remove = None

            with col4:
                st.write("")
                st.write("")
                if tag_to_remove and st.button("Убрать тег", key=f"btn_rm_tag_{post.id}"):
                    if remove_tag_from_post(post.id, tag_to_remove):
                        st.rerun()

            # Секция управления самой записью (вынесена в отдельную строку для защиты от случайных кликов)
            col_del1, col_del2 = st.columns([8, 2])
            with col_del2:
                # Выделение деструктивного действия акцентным цветом (type="primary")
                if st.button("Удалить запись", key=f"btn_del_{post.id}", type="primary"):
                    if delete_post_from_db(post.id):
                        st.rerun()