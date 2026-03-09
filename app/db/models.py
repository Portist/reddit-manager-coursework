"""
Слой данных: Описание объектно-реляционной модели (ORM) предметной области.
Определяет сущности базы данных и связи между ними.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Базовый класс декларативной разметки SQLAlchemy."""
    pass


# Ассоциативная таблица для реализации связи Many-to-Many.
# Составной первичный ключ (post_id, tag_id) гарантирует уникальность привязки на уровне СУБД.
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', String, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Post(Base):
    """
    Сущность сохраненной записи (поста), агрегированной из внешнего источника.
    """
    __tablename__ = 'posts'

    # Уникальный идентификатор (хеш) платформы-источника используется как PK
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String)
    subreddit = Column(String)

    # Двунаправленная навигационная связь (bidirectional relationship) с сущностью Tag
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')


class Tag(Base):
    """
    Сущность пользовательской категории (тега) для реализации механизма фолксономии.
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Ограничение unique=True предотвращает создание семантических дубликатов в БД
    name = Column(String, unique=True, nullable=False)

    # Обратная связь для получения списка всех постов по конкретному тегу
    posts = relationship('Post', secondary=post_tags, back_populates='tags')