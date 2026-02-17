from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extension import db


class Telephone(db.Model):
    __tablename__ = "telephone"

    telephone_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telephone_type_id: Mapped[int] = mapped_column(
        ForeignKey("telephone_type.telephono_type_id", nullable=False)
    )
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person_id"), nullable=False
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_principal: Mapped[bool] = mapped_column(Boolean, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    person = relationship("Person", back_populates="telephones")
    telephone_type = relationship("Telephone_type", back_populates="telephone")
