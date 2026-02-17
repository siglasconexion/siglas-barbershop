from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.extensions import db


class Payment(db.Model):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(primaty_key=True, autoincrement=True)
    payment_type_id: Mapped[int] = mapped_column(
        ForeignKey("payment_type.payment_type_id"), nullable=False
    )
    barber_id: Mapped[int] = mapped_column(nullable=True)
    client_id: Mapped[int] = mapped_column(nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=DateTime.utcnow, onupdate=DateTime.utcnow
    )

    payment_type = relationship("Payment_type", back_populate="payment")
