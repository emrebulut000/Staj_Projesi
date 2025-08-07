# models.py - cascade eklenmiş tam hali

from sqlalchemy import (Boolean, Column, Integer, String, Date, ForeignKey, 
                        JSON, create_engine, DateTime, UniqueConstraint, Time)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    department = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager = relationship("User", remote_side=[id], backref="subordinates")

    # --- DEĞİŞİKLİKLER BU SATIRLARDA ---
    # Bir kullanıcı silindiğinde, ona ait bu kayıtlar da otomatik silinsin.
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")
    overtime_requests = relationship("OvertimeRequest", back_populates="user", cascade="all, delete-orphan")
    logins = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")

class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    meal_type = Column(String, nullable=False)
    menu_items = Column(JSON)
    salad_bar = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('date', 'meal_type', name='_date_meal_type_uc'),)

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    will_attend = Column(Boolean, default=True)
    user = relationship("User", back_populates="attendances")
    __table_args__ = (UniqueConstraint('user_id', 'date', name='_user_id_date_uc'),)

class OvertimeRequest(Base):
    __tablename__ = "overtime_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String, nullable=False)
    department = Column(String, nullable=False) 
    status = Column(String, default="Yönetici Onayı Bekliyor") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="overtime_requests")

class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    login_timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logins")

engine = create_engine("sqlite:///./instance/site.db", connect_args={"check_same_thread": False})