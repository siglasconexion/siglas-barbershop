from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Appointment(db.Model):
    __tablename__ = "appointment"

    appointment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status_appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointment_status.appointment_status_id"), nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.client_id"), nullable=False
    )
    barber_id: Mapped[int] = mapped_column(
        ForeignKey("barber.barber_id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.service_id"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    final_price: Mapped[float] = mapped_column(Numeric(10, 0), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    status = relationship("Appointment_status", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")
    barber = relationship("Barber", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
