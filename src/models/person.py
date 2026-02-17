from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Person(db.Model):
    __tablename__ = "person"
    person_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_type_id: Mapped[int] = mapped_column(
        ForeignKey("person_type.person_type_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(140), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    person_type = relationship("Person_type", back_populates="persons")
    barbers = relationship("Barber", back_populates="person")
    clients = relationship("Client", back_populates="person")
    emails = relationship("Email", back_populates="person")
    telephones = relationship("Telephone", back_populates="person")
    social_medias = relationship("Social_media", back_populates="person")
    users = relationship("User", back_populates="user")

    def serialize(self):
        return {
            "person_id": self.person_id,
            "person_type_id": self.person_type_id,
            "name": self.name,
            "address": self.address,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }
