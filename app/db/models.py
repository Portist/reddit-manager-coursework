"""
Слой данных: Описание объектно-реляционной модели предметной области.
Определяет сущности базы данных, их атрибуты и правила связей между ними.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    """Базовый класс, от которого наследуются все декларативные модели таблиц."""
    pass

# Вспомогательная ассоциативная таблица для реализации связи "Многие-ко-многим".
# Позволяет привязывать множество тегов к множеству публикаций и наоборот.
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', String, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Post(Base):
    """
    Сущность сохраненной публикации, извлеченной из внешнего источника.
    Представляет собой центральный элемент системы хранения.
    """
    __tablename__ = 'posts'

    # Уникальный идентификатор платформы-источника используется как первичный ключ
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String)
    subreddit = Column(String)

    # Прямая ссылка на медиафайл (изображение или видео), если он присутствует в публикации
    media_url = Column(String, nullable=True)

    # Полное текстовое содержимое публикации (может отсутствовать для медиа-постов)
    selftext = Column(String, nullable=True)

    # Флаг логического удаления (перемещение в виртуальную корзину)
    is_deleted = Column(Boolean, default=False)

    # Флаг состояния обработки публикации пользователем (прочитано/новое)
    is_read = Column(Boolean, default=False)

    # Флаг выделения приоритетной или избранной публикации
    is_starred = Column(Boolean, default=False)

    # Двунаправленная навигационная связь с таблицей категорий (тегов)
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')

class Tag(Base):
    """
    Сущность категории для семантической организации публикаций.
    Может быть создана пользователем вручную или сгенерирована алгоритмически.
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Строгое ограничение уникальности предотвращает дублирование категорий на уровне СУБД
    name = Column(String, unique=True, nullable=False)

    # Обратная навигационная связь для получения списка публикаций, привязанных к категории
    posts = relationship('Post', secondary=post_tags, back_populates='tags')