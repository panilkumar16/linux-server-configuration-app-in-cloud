# Configuration
import sys

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
# For configuration and class code
from sqlalchemy.ext.declarative import declarative_base
# To create our ForeignKey relationships
from sqlalchemy.orm import relationship
# For configuration code at the end of the file
from sqlalchemy import create_engine

# Letting sqlalchemy know our classes are special sqlalchemy classes
# that correspond to tables in our database
Base = declarative_base()

# Class
# Representation of table as a python class
# Extends the Base Class
# Nested inside will be table and mapper code
# Table
# Table representation
# Syntax:
# __tablename__ = 'table_name'
# Mapper
# Maps python objects to columns in our database
# Syntax:
# columnName = Column(attributes, ...)
# example attributes:
# String(250)
# Integer
# relationship(Class)
# nullable = False
# primary_key = True
# ForeignKey('table_name.id')


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    created_datetime = Column(DateTime, default=func.now())
    items = relationship("Item", cascade="all, delete-orphan")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
        }

    @property
    def serializeWithItems(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'items': [item.serializeForCategory for item in self.items],
        }


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250))
    created_datetime = Column(DateTime, default=func.now())
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Category")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'category_id': self.category_id,
            'id': self.id,
            'title': self.title,
            'description': self.description,
        }

    @property
    def serializeForCategory(self):
        # Returns object data in easily serializeable format
        return {
            'category_id': self.category_id,
            'description': self.description,
            'id': self.id,
            'title': self.title,
        }

# Configuration: insert at end of the file

# Point to the database we use
#engine = create_engine('sqlite:///catalog1.db')
engine = create_engine('postgresql://catalog:P@ssW0rd@localhost/catalog')

# Going to the database and add the classes we create as new tables
# to the database
Base.metadata.create_all(engine)
