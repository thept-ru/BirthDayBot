from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///birthday_bot.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserBirthday(Base):
    """Model to store user birthday information scoped per chat"""
    __tablename__ = "user_birthdays"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    username = Column(String, nullable=True)  # Store username for greeting message
    day = Column(Integer, nullable=False)  # Day of month (1-31)
    month = Column(Integer, nullable=False)  # Month (1-12)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure unique (user_id, chat_id) combination
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_user_chat"),)

    def __repr__(self):
        return f"<UserBirthday(user_id={self.user_id}, chat_id={self.chat_id}, date={self.day}.{self.month:02d})>"


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
