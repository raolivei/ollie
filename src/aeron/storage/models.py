from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="session")

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    speaker: Mapped[str] = mapped_column(String(50))  # "User", "Aeron"
    transcript: Mapped[str] = mapped_column(Text)
    audio_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ChromaDB ID

    session: Mapped["Session"] = relationship(back_populates="conversations")

class Metadata(Base):
    __tablename__ = "metadata"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(Text)

