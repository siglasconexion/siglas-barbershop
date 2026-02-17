from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Telephone_type(db.Model):
    __tablename__ = "telephone_type"

    telephone_type_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nuallable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    telephone = relationship("Telephone", back_populate="telephone_type")
