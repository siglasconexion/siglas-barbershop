from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Role_type(db.Model):
    __tablename__ = "role_type"

    role_type_id: Mapped[int] = mapped_column(primaty_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    user = relationship("User", back_populates="role_type")
