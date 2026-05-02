"""
Модуль уровня доступа к данным.
Реализует операции создания, чтения, обновления и удаления
для моделей данных с использованием объектно-реляционного отображения.
"""
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from app.db.models import Post, Tag, Base
from app.db.database import engine, SessionLocal

def init_db() -> None:
    """Инициализирует структуру базы данных на основе декларативных моделей."""
    Base.metadata.create_all(bind=engine)
    print("INFO: База данных успешно инициализирована.")

def save_reddit_posts_to_db(posts_data: list[dict]) -> int:
    """
    Сохраняет список извлеченных записей в локальное хранилище.
    Проверяет наличие дубликатов по уникальному идентификатору перед добавлением новой записи.

    :param posts_data: Список словарей с метаданными публикаций.
    :return: Количество успешно добавленных новых записей.
    """
    db: Session = SessionLocal()
    saved_count = 0
    try:
        for p_data in posts_data:
            existing_post = db.query(Post).filter(Post.id == p_data['id']).first()
            if not existing_post:
                new_post = Post(
                    id=p_data['id'],
                    title=p_data['title'],
                    url=p_data['url'],
                    subreddit=p_data['subreddit'],
                    media_url=p_data.get('media_url'),
                    selftext=p_data.get('selftext')
                )
                db.add(new_post)
                saved_count += 1
        db.commit()
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"ERROR: Ошибка транзакции при сохранении публикаций: {e}")
        return 0
    finally:
        db.close()

def get_all_posts() -> list[Post]:
    """
    Извлекает все активные записи из базы данных.
    Применяет предварительную загрузку связанных категорий для оптимизации последующих обращений.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags)).filter(Post.is_deleted == False).all()
    finally:
        db.close()

def get_all_tags() -> list[Tag]:
    """Возвращает список всех существующих пользовательских и автоматических категорий."""
    db: Session = SessionLocal()
    try:
        return db.query(Tag).all()
    finally:
        db.close()

def add_tag_to_post(post_id: str, tag_name: str) -> bool:
    """
    Назначает категорию выбранной публикации.
    Автоматически регистрирует новую категорию, если она отсутствует в системе.

    :param post_id: Идентификатор целевой записи.
    :param tag_name: Текстовое название присваиваемой категории.
    :return: Статус успешности операции.
    """
    db: Session = SessionLocal()
    try:
        tag_name = tag_name.strip().lower()
        if not tag_name: return False

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post: return False

        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            # Принудительная отправка данных для получения идентификатора новой категории
            db.flush()

        if tag not in post.tags:
            post.tags.append(tag)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()


def search_posts_advanced(search_query: str, search_areas: list[str]) -> list[Post]:
    """
    Выполняет полнотекстовый поиск с динамическим формированием условий фильтрации.

    :param search_query: Поисковая фраза.
    :param search_areas: Список атрибутов базы данных для осуществления поиска.
    :return: Список найденных публикаций, удовлетворяющих критериям.
    """
    db: Session = SessionLocal()
    try:
        formatted_query = f"%{search_query}%"
        conditions = []

        # Динамическое добавление регистронезависимых проверок в зависимости от выбранных зон поиска
        if "Заголовки" in search_areas:
            conditions.append(Post.title.ilike(formatted_query))
        if "Сабреддиты" in search_areas:
            conditions.append(Post.subreddit.ilike(formatted_query))
        if "Ссылки" in search_areas:
            conditions.append(Post.url.ilike(formatted_query))

        if not conditions:
            return []

        # Распаковка собранных условий для логического объединения
        return db.query(Post).options(selectinload(Post.tags)).filter(
            or_(*conditions)
        ).all()

    except Exception as e:
        print(f"ERROR: Ошибка при выполнении расширенного поиска: {e}")
        return []
    finally:
        db.close()

def delete_post_from_db(post_id: str) -> bool:
    """Осуществляет логическое удаление записи посредством установки соответствующего флага состояния."""
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.is_deleted = True
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def delete_posts_bulk(post_ids: list[str]) -> int:
    """Выполняет массовое логическое удаление группы выбранных записей."""
    db: Session = SessionLocal()
    try:
        updated = db.query(Post).filter(Post.id.in_(post_ids)).update({Post.is_deleted: True}, synchronize_session=False)
        db.commit()
        return updated
    except Exception as e:
        db.rollback()
        return 0
    finally:
        db.close()

def get_deleted_posts() -> list[Post]:
    """Извлекает полный список публикаций, помеченных пользователем на удаление."""
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags)).filter(Post.is_deleted == True).all()
    finally:
        db.close()

def restore_post_in_db(post_id: str) -> bool:
    """Отменяет логическое удаление записи, возвращая ее в основной список системы."""
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.is_deleted = False
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def restore_posts_bulk(post_ids: list[str]) -> int:
    """Выполняет пакетное восстановление множества ранее удаленных записей."""
    db: Session = SessionLocal()
    try:
        updated = db.query(Post).filter(Post.id.in_(post_ids)).update({Post.is_deleted: False}, synchronize_session=False)
        db.commit()
        return updated
    except Exception as e:
        db.rollback()
        return 0
    finally:
        db.close()

def remove_tag_from_post(post_id: str, tag_name: str) -> bool:
    """
    Разрывает ассоциативную связь между публикацией и назначенным ей тегом.
    Удаляет сам объект категории из системы, если он больше не имеет привязок к записям.
    """
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if post and tag and tag in post.tags:
            post.tags.remove(tag)

            # Сборка мусора для изоляции неиспользуемых данных
            if len(tag.posts) == 0:
                db.delete(tag)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def delete_tags_bulk(auto_only: bool = True) -> int:
    """
    Реализует механизм массовой очистки классификатора.
    Предварительно уничтожает связи с публикациями для сохранения ссылочной целостности базы.

    :param auto_only: Булево значение для ограничения области удаления сгенерированными категориями.
    :return: Общее количество удаленных категорий.
    """
    db: Session = SessionLocal()
    deleted_count = 0
    try:
        query = db.query(Tag)
        if auto_only:
            query = query.filter(Tag.name.like("auto:%"))
        tags_to_delete = query.all()
        for tag in tags_to_delete:
            tag.posts = []
            db.delete(tag)
            deleted_count += 1
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        return 0
    finally:
        db.close()


# Блок управления статусами и фильтрации состояний публикаций

def update_post_read_status(post_id: str, is_read: bool) -> bool:
    """Модифицирует статус прочтения для одиночной записи."""
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.is_read = is_read
            db.commit()
            return True
        return False
    finally:
        db.close()

def mark_posts_as_read_bulk(post_ids: list[str], is_read: bool) -> int:
    """Применяет новый статус прочтения к массиву идентификаторов записей за одну транзакцию."""
    db: Session = SessionLocal()
    try:
        updated = db.query(Post).filter(Post.id.in_(post_ids)).update({Post.is_read: is_read}, synchronize_session=False)
        db.commit()
        return updated
    finally:
        db.close()

def update_post_star_status(post_id: str, is_starred: bool) -> bool:
    """Изменяет статус избранного для указанной целевой публикации."""
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.is_starred = is_starred
            db.commit()
            return True
        return False
    finally:
        db.close()

def mark_posts_as_starred_bulk(post_ids: list[str], is_starred: bool) -> int:
    """Выполняет пакетное изменение статуса избранного для переданного списка элементов."""
    db: Session = SessionLocal()
    try:
        updated = db.query(Post).filter(Post.id.in_(post_ids)).update({Post.is_starred: is_starred}, synchronize_session=False)
        db.commit()
        return updated
    finally:
        db.close()

def get_posts_by_status(is_read: bool = False, is_deleted: bool = False) -> list[Post]:
    """
    Осуществляет выборку записей на основе комбинации их состояний прочтения и удаления.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags))\
            .filter(Post.is_read == is_read, Post.is_deleted == is_deleted).all()
    finally:
        db.close()

def get_starred_posts() -> list[Post]:
    """Извлекает коллекцию всех активных публикаций, которые были добавлены пользователем в избранное."""
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags))\
            .filter(Post.is_starred == True, Post.is_deleted == False).all()
    finally:
        db.close()