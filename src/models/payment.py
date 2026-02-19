from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Payment(db.Model):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_type_id: Mapped[int] = mapped_column(
        ForeignKey("payment_type.payment_type_id"), nullable=False
    )
    barber_id: Mapped[int] = mapped_column(nullable=True)
    client_id: Mapped[int] = mapped_column(nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    payment_type = relationship("Payment_type", back_populates="payment")
