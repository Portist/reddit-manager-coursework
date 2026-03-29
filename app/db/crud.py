"""
Модуль уровня доступа к данным (Data Access Layer).
Реализует операции создания, чтения, обновления и удаления (CRUD)
для сущностей Post и Tag с использованием SQLAlchemy ORM.
"""
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from app.db.models import Post, Tag, Base
from app.db.database import engine, SessionLocal


def init_db() -> None:
    """Создает все необходимые таблицы в базе данных на основе описанных моделей."""
    Base.metadata.create_all(bind=engine)
    print("INFO: База данных успешно инициализирована.")


def save_reddit_posts_to_db(posts_data: list[dict]) -> int:
    """
    Сохраняет извлеченные записи в локальную базу данных.
    Игнорирует уже существующие записи во избежание дублирования данных.

    :param posts_data: Список словарей с метаданными записей.
    :return: Количество успешно добавленных новых записей.
    """
    db: Session = SessionLocal()
    saved_count = 0
    try:
        for p_data in posts_data:
            # Проверка наличия записи по её уникальному идентификатору
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

        # Фиксация изменений в базе данных (завершение транзакции)
        db.commit()
        return saved_count
    except Exception as e:
        # Откат изменений в случае непредвиденной ошибки
        db.rollback()
        print(f"ERROR: Ошибка транзакции при сохранении постов: {e}")
        return 0
    finally:
        # Обязательное закрытие сессии для освобождения ресурсов
        db.close()


def get_all_posts() -> list[Post]:
    """
    Извлекает все активные (не удаленные) записи из базы.
    Использует предварительную загрузку (selectinload) для связанных тегов,
    что предотвращает проблему избыточных запросов (N+1) при отображении интерфейса.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags)).filter(Post.is_deleted == False).all()
    except Exception as e:
        print(f"ERROR: Ошибка при извлечении постов: {e}")
        return []
    finally:
        db.close()


def get_all_tags() -> list[Tag]:
    """Возвращает список всех существующих пользовательских категорий."""
    db: Session = SessionLocal()
    try:
        return db.query(Tag).all()
    finally:
        db.close()


def add_tag_to_post(post_id: str, tag_name: str) -> bool:
    """
    Назначает тег указанной записи.
    Если тега с таким именем не существует, он создается автоматически.

    :param post_id: Идентификатор целевой записи.
    :param tag_name: Название тега (будет приведено к нижнему регистру).
    :return: Успешность операции (True/False).
    """
    db: Session = SessionLocal()
    try:
        tag_name = tag_name.strip().lower()
        if not tag_name:
            return False

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False

        # Поиск существующего тега или создание нового
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            # Принудительная отправка SQL-запроса для получения ID нового тега
            db.flush()

        # Проверка на дублирование перед привязкой
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
    Выполняет полнотекстовый поиск подстроки в заголовках И названиях сообществ (сабреддитов).
    Оптимизировано на уровне базы данных с использованием оператора поиска без учета регистра (ILIKE)
    и логического ветвления (OR).
    """
    db: Session = SessionLocal()
    try:
        formatted_query = f"%{search_query}%"
        return db.query(Post) \
            .options(selectinload(Post.tags)) \
            .filter(
            # Использование оператора or_ для расширения области поиска на две колонки
            or_(
                Post.title.ilike(formatted_query),
                Post.subreddit.ilike(formatted_query)
            ),
            Post.is_deleted == False
        ) \
            .all()
    except Exception as e:
        print(f"ERROR: Ошибка при поиске '{search_query}': {e}")
        return []
    finally:
        db.close()


def delete_post_from_db(post_id: str) -> bool:
    """
    Логическое удаление: помечает запись как удаленную, не стирая её физически из таблицы.
    Это необходимо для безопасной работы корзины и предотвращения повторной загрузки.
    """
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
        print(f"ERROR: Ошибка при удалении поста {post_id}: {e}")
        return False
    finally:
        db.close()


def get_deleted_posts() -> list[Post]:
    """Извлекает записи, которые были перемещены пользователем в корзину."""
    db: Session = SessionLocal()
    try:
        return db.query(Post).options(selectinload(Post.tags)).filter(Post.is_deleted == True).all()
    finally:
        db.close()


def restore_post_in_db(post_id: str) -> bool:
    """Восстанавливает запись из корзины, возвращая её в основной список."""
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


def remove_tag_from_post(post_id: str, tag_name: str) -> bool:
    """
    Удаляет связь между указанной записью и категорией (тегом).
    Реализует механизм сборки мусора (Garbage Collection): если после удаления
    тег больше не привязан ни к одной записи, он удаляется из базы данных.

    :param post_id: Идентификатор целевой записи.
    :param tag_name: Название тега для удаления.
    :return: Успешность операции (True/False).
    """
    db: Session = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False

        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        # Если тег найден и он действительно привязан к этому посту
        if tag and tag in post.tags:
            post.tags.remove(tag)

            # Если этот тег больше не привязан ни к одному посту - удаляем его насовсем
            if len(tag.posts) == 0:
                db.delete(tag)

            db.commit()
            return True

        return False
    except Exception as e:
        db.rollback()
        print(f"ERROR: Ошибка при удалении тега '{tag_name}' у записи {post_id}: {e}")
        return False
    finally:
        db.close()