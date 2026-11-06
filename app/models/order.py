from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.db.base import Base
from app.models.timestamp_mixin import TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    user = relationship("User", back_populates="orders")

    items = relationship(
        "OrderItems",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    