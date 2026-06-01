from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, BigInteger
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    telegram_bot_id = Column(BigInteger, unique=True, nullable=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    token = Column(String, nullable=True)
    status = Column(String, default="connected")
    messages_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String)
    text = Column(Text, nullable=False)
    summary = Column(Text)
    sentiment = Column(String, default="neutral")
    emotion = Column(String, default="neutral")
    priority = Column(String, default="medium")
    category = Column(String, default="general")
    complaint = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
