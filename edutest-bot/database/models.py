import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class RoleEnum(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT, nullable=False)
    full_name = Column(String, nullable=True)
    group_name = Column(String, nullable=True)

    tests_created = relationship("Test", back_populates="author")
    results = relationship("Result", back_populates="user")
    managed_groups = relationship("StudentGroup", back_populates="teacher")

class GroupChat(Base):
    __tablename__ = 'group_chats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    group_name = Column(String, nullable=False)

class StudentGroup(Base):
    __tablename__ = 'student_groups'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    teacher = relationship("User", back_populates="managed_groups")

class Championship(Base):
    __tablename__ = 'championships'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    tests = relationship("Test", back_populates="championship")

class Test(Base):
    __tablename__ = 'tests'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Acts as the test code
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    correct_answers = Column(String, nullable=False)  # e.g., "ABCD"
    file_id = Column(String, nullable=True)  # Telegram file ID
    time_limit = Column(Integer, nullable=True)  # In minutes
    is_active = Column(Boolean, default=True)
    championship_id = Column(Integer, ForeignKey('championships.id'), nullable=True)

    author = relationship("User", back_populates="tests_created")
    championship = relationship("Championship", back_populates="tests")
    results = relationship("Result", back_populates="test")

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    student_answers = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")
    test = relationship("Test", back_populates="results")
