"""
Модуль Data Access Layer (DAL) для работы с локальной базой данных SQLite.
Реализует CRUD-операции для сущностей Post и Tag с использованием SQLAlchemy ORM.
"""
from sqlalchemy.orm import Session, selectinload
from app.db.models import Post, Tag, Base
from app.db.database import engine, SessionLocal


def init_db() -> None:
    """Инициализирует схему базы данных, создавая отсутствующие таблицы."""
    Base.metadata.create_all(bind=engine)
    print("INFO: База данных успешно инициализирована.")


def save_reddit_posts_to_db(posts_data: list[dict]) -> int:
    """
    Синхронизирует полученные из внешнего источника посты с локальной БД.
    Игнорирует существующие записи во избежание дублирования.

    :param posts_data: Список словарей с метаданными постов.
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
                    subreddit=p_data['subreddit']
                )
                db.add(new_post)
                saved_count += 1
        db.commit()
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"ERROR: Ошибка транзакции при сохранении постов: {e}")
        return 0
    finally:
        db.close()


def get_all_posts() -> list[Post]:
    """
    Извлекает все сохраненные посты.
    Использует eager loading (selectinload) для связанных тегов,
    предотвращая проблему N+1 запросов и DetachedInstanceError на уровне представления.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags)).all()
    except Exception as e:
        print(f"ERROR: Ошибка при извлечении постов: {e}")
        return []
    finally:
        db.close()


def get_all_tags() -> list[Tag]:
    """Возвращает список всех уникальных пользовательских тегов."""
    db: Session = SessionLocal()
    try:
        return db.query(Tag).all()
    finally:
        db.close()


def add_tag_to_post(post_id: str, tag_name: str) -> bool:
    """
    Присваивает тег указанному посту.
    Реализует паттерн 'get_or_create' для сущности Tag перед привязкой.

    :param post_id: Идентификатор поста.
    :param tag_name: Название тега (будет приведено к нижнему регистру).
    :return: True, если тег успешно добавлен, иначе False.
    """
    db: Session = SessionLocal()
    try:
        tag_name = tag_name.strip().lower()
        if not tag_name:
            return False

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False

        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            # flush используется для получения ID тега до коммита транзакции
            db.flush()

        if tag not in post.tags:
            post.tags.append(tag)
            db.commit()
            return True

        return False
    except Exception as e:
        db.rollback()
        print(f"ERROR: Ошибка при привязке тега '{tag_name}' к посту {post_id}: {e}")
        return False
    finally:
        db.close()


def search_posts_by_title(search_query: str) -> list[Post]:
    """
    Выполняет полнотекстовый поиск подстроки в заголовках постов (case-insensitive).
    Оптимизировано на уровне СУБД с использованием оператора ILIKE.
    """
    db: Session = SessionLocal()
    try:
        formatted_query = f"%{search_query}%"
        return db.query(Post)\
            .options(selectinload(Post.tags))\
            .filter(Post.title.ilike(formatted_query))\
            .all()
    except Exception as e:
        print(f"ERROR: Ошибка при поиске '{search_query}': {e}")
        return []
    finally:
        db.close()


def delete_post_from_db(post_id: str) -> bool:
    """
    Удаляет пост из локальной базы данных.
    Каскадное удаление связей в таблице post_tags обеспечивается настройками ORM.
    """
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"ERROR: Ошибка при удалении поста {post_id}: {e}")
        return False
    finally:
        db.close()