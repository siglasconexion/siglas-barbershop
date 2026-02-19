from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Service(db.Model):
    __tablename__ = "service"

    service_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_type_id: Mapped[int] = mapped_column(
        ForeignKey("service_type.service_type_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 0), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    service_type = relationship("Service_type", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")
