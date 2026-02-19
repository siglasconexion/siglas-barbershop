from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Client(db.Model):
    __tablename__ = "client"

    client_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person_id"), nullable=False
    )
    barber_id: Mapped[int] = mapped_column(
        ForeignKey("barber.barber_id"), nullable=False
    )
    last_visit: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    person = relationship("Person", back_populates="clients")
    appointments = relationship("Appointment", back_populates="client")
    barber = relationship("Barber", back_populates="clients")
