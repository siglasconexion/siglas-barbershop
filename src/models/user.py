from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class User(db.Model):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primety_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person_id"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("role_type.role_type_id"), nullable=False
    )
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    role_type = relationship("Role_type", back_populates="user")
    user = relationship("User", back_populates="users")
