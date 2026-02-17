from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Email(db.Model):
    __tablename__ = "email"

    email_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person_id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    is_principal: Mapped[int] = mapped_column(Boolean, nullable=False)
    type: Mapped[str] = mapped_column(String(25), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )
    person = relationship("Person", back_populates="emails")
