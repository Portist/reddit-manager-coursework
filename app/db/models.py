"""
Слой данных: Описание объектно-реляционной модели (ORM) предметной области.
Определяет сущности базы данных, их атрибуты и правила связей между ними.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Базовый класс, от которого наследуются все модели таблиц."""
    pass


# Вспомогательная ассоциативная таблица для реализации связи "Многие-ко-многим" (Many-to-Many).
# Составной первичный ключ (post_id + tag_id) гарантирует, что одному посту
# нельзя назначить один и тот же тег дважды на уровне самой базы данных.
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', String, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Post(Base):
    """
        Сущность сохраненной записи, извлеченной из внешнего источника.
    """
    __tablename__ = 'posts'

    # Уникальный идентификатор платформы-источника используется как первичный ключ
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String)
    subreddit = Column(String)

    # Флаг логического (мягкого) удаления.
    # Если значение True, пост считается удаленным и скрывается из основного списка.
    is_deleted = Column(Boolean, default=False)

    # Двунаправленная связь с таблицей тегов
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')


class Tag(Base):
    """
    Сущность пользовательской категории (тега) для организации записей.
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Ограничение unique=True предотвращает создание дубликатов с одинаковым именем
    name = Column(String, unique=True, nullable=False)

    # Обратная связь для получения списка всех постов, привязанных к конкретному тегу
    posts = relationship('Post', secondary=post_tags, back_populates='tags')