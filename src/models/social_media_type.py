from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Social_media_type(db.Model):
    __tablaname__ = "social_media_type"

    social_media_type: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    icon: Mapped[str] = mapped_column(String(25), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    social_media = relationship("Social_media", back_populates="social_media_type")
