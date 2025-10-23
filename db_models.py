# db_models.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import config  # читаем настройки из config.py

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    program = Column(String(128), nullable=False)
    year = Column(Integer, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    homeworks = relationship('Homework', back_populates='student', cascade='all, delete-orphan')
    grades = relationship('Grade', back_populates='student', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class ScheduleItem(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    program = Column(String(128), nullable=False)
    week_day = Column(String(32), nullable=False)  # e.g. Monday
    time = Column(String(64), nullable=False)
    subject = Column(String(255), nullable=False)
    classroom = Column(String(64), nullable=True)
    teacher = Column(String(128), nullable=True)

class Homework(Base):
    __tablename__ = 'homeworks'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    program = Column(String(128), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    pushed = Column(Integer, default=0)
    attachment = Column(String(512), nullable=True)

    student = relationship('Student', back_populates='homeworks')

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject = Column(String(255), nullable=False)
    grade = Column(String(32), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship('Student', back_populates='grades')

def get_database_url():
    if getattr(config, "DATABASE_URL", None):
        return config.DATABASE_URL
    user = getattr(config, "MYSQL_USER", "student_user")
    password = getattr(config, "MYSQL_PASSWORD", "student_pass")
    host = getattr(config, "MYSQL_HOST", "127.0.0.1")
    port = getattr(config, "MYSQL_PORT", 3306)
    db = getattr(config, "MYSQL_DB", "student_dashboard")
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4'

def get_engine():
    db_url = get_database_url()
    return create_engine(db_url, echo=False, future=True, pool_pre_ping=True)

def get_session(engine=None):
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False)
    return Session()
