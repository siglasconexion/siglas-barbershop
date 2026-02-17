from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Social_media(db.Model):
    __tqblaname__ = "social_media"

    social_media_id: Mapped[int] = mapped_column(primery_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person_id"), nullable=True
    )
    social_media_type_id: Mapped[int] = mapped_column(
        ForeignKey("social_media_type.social_media_type_id"), nullable=True
    )
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(120), nullable=True)
    is_principal: Mapped[bool] = mapped_column(Boolean, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    person = relationship("Person", back_populates="social_medias")
    social_media_type = relationship("Social_media_type", back_populates="social_media")
