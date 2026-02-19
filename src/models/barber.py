from datetime import datetime, timezone
from sqlalchemy import DateTime, String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Barber(db.Model):
    __tablename__ = "barber"

    barber_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.person.id"), nullable=False
    )
    barber_type_id: Mapped[int] = mapped_column(
        ForeignKey("barber_type.barber_type_id"), nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    salary: Mapped[float] = mapped_column(Numeric(10, 0), nullable=False)
    contract_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    schedule: Mapped[str] = mapped_column(String(100), nullable=False)

    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    person = relationship("Person", back_populates="barbers")
    barber_type = relationship("Barber_type", back_populates="barbers")
    appointments = relationship("Appointment", back_populates="barber")
    clients = relationship("Client", back_populates="barber")
