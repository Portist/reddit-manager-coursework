"""
Модуль изолированных компонентов пользовательского интерфейса.
Предоставляет набор функций для стандартизированной отрисовки
интерактивных элементов и блоков контента на веб-странице.
"""
import streamlit as st
from app.db.crud import (
    add_tag_to_post, delete_post_from_db, restore_post_in_db,
    remove_tag_from_post, update_post_read_status, update_post_star_status
)

def render_post_card(post, is_trash_mode: bool = False) -> None:
    """
    Формирует и отображает интерактивную визуальную карточку для отдельной публикации.
    Реализует элементы управления состояниями (прочитано/избранное) и интерфейс для массовых действий.

    :param post: Объект публикации из базы данных.
    :param is_trash_mode: Флаг отображения карточки в режиме "Корзина" для адаптации доступных действий.
    """
    current_tags = [t.name for t in post.tags]
    tags_str = ", ".join(current_tags) if current_tags else "Нет категорий"

    # Визуальный индикатор непрочитанной записи
    unread_indicator = "[НОВОЕ] " if not post.is_read and not is_trash_mode else ""

    # Использование моноширинных типографических символов для предотвращения смещения верстки
    star_icon = "★" if post.is_starred else "☆"

    card_label = f"{unread_indicator}[{post.subreddit}] {post.title}"
    clean_url = post.url.replace("old.reddit.com", "www.reddit.com") if post.url else "#"

    # Разделение пространства карточки на колонки: чекбокс, кнопка статуса и основной контент
    col_chk, col_star, col_exp = st.columns([0.5, 0.5, 11])

    with col_chk:
        # Привязка чекбокса к глобальному состоянию сессии для поддержки массовых операций
        st.checkbox(" ", key=f"chk_{post.id}", label_visibility="collapsed")

    with col_star:
        # Кнопка переключения статуса "Избранное"
        if st.button(star_icon, key=f"btn_star_{post.id}", help="Пометить/Снять метку"):
            update_post_star_status(post.id, not post.is_starred)
            st.rerun()

    with col_exp:
        # Раскрывающийся блок (аккордеон) для скрытия объемного контента
        with st.expander(card_label):
            st.markdown(f"**Ссылка:** [Открыть на Reddit]({clean_url})")
            st.markdown(f"**Теги:** `{tags_str}`")

            st.markdown("---")

            # Блок рендеринга извлеченного текстового содержимого
            if post.selftext:
                with st.expander("Читать текст записи"):
                    st.write(post.selftext)

            # Блок рендеринга прикрепленных медиафайлов
            if post.media_url:
                media_links = post.media_url.split("|")
                expander_title = "Показать медиафайл" if len(media_links) == 1 else f"Показать галерею ({len(media_links)} фото)"

                with st.expander(expander_title):
                    for link in media_links:
                        try:
                            # Маршрутизация метода отрисовки в зависимости от типа медиаконтента
                            if ".mp4" in link or "fallback_url" in link:
                                st.video(link)
                            else:
                                st.image(link, use_container_width=True)
                        except Exception:
                            st.caption("Ошибка: медиафайл больше недоступен на сервере источника.")

            # Блок индивидуальных элементов управления публикацией
            if is_trash_mode:
                if st.button("Восстановить", key=f"btn_res_{post.id}", type="primary"):
                    if restore_post_in_db(post.id):
                        st.rerun()
            else:
                col_actions, col_tags = st.columns([1, 1])

                with col_actions:
                    st.markdown("**Действия**")
                    if not post.is_read:
                        if st.button("Отметить прочитанным", key=f"read_{post.id}"):
                            update_post_read_status(post.id, True)
                            st.rerun()
                    else:
                        if st.button("Вернуть в Новое", key=f"unread_{post.id}"):
                            update_post_read_status(post.id, False)
                            st.rerun()

                    if st.button("В корзину", key=f"del_{post.id}", type="primary"):
                        if delete_post_from_db(post.id):
                            st.rerun()

                with col_tags:
                    st.markdown("**Управление тегами**")
                    new_tag = st.text_input("Добавить тег:", key=f"input_{post.id}")
                    if st.button("Добавить", key=f"btn_add_{post.id}"):
                        if new_tag and add_tag_to_post(post.id, new_tag):
                            st.rerun()

                    if current_tags:
                        tag_to_remove = st.selectbox("Удалить тег:", current_tags, key=f"sel_rm_{post.id}")
                        if st.button("Убрать тег", key=f"btn_rm_{post.id}"):
                            if remove_tag_from_post(post.id, tag_to_remove):
                                st.rerun()