from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey, JSON, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    attendances = relationship("Attendance", back_populates="user")

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    meal_type = Column(String)  # "Ogle_Yemegi" veya "Aksam_Yemegi"
    menu_items = Column(JSON)  # Çorba, Ana Yemek, Yan Yemek, Tatlı
    salad_bar = Column(JSON)   # Salata bilgileri

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meals = relationship("Meal", back_populates="category")

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    calories = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    category = relationship("Category", back_populates="meals")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    will_attend = Column(Boolean, default=True)
    user = relationship("User", back_populates="attendances")

# Veritabanı bağlantısı
engine = create_engine("sqlite:///./instance/site.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
