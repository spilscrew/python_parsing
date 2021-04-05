from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime

Base = declarative_base()


class UrlMixin:
    url = Column(String, nullable=False, unique=True)


class IdMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


class DateTimeMixin:
    created_at = Column(DateTime)


class NameMixin:
    name = Column(String)


tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Post(Base, UrlMixin, IdMixin, DateTimeMixin):
    __tablename__ = 'posts'
    title = Column(String, nullable=False)
    image = Column(String)
    author_id = Column(Integer, ForeignKey('authors.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary=tag_post)


class Author(Base, UrlMixin, IdMixin, NameMixin):
    __tablename__ = 'authors'
    posts = relationship('Post', viewonly=True)


class Tag(Base, UrlMixin, IdMixin, NameMixin):
    __tablename__ = 'tags'
    posts = relationship(Post, secondary=tag_post, viewonly=True)


class Comments(Base, UrlMixin, IdMixin, NameMixin):
    __tablename__ = 'comments'
    text = Column(String)