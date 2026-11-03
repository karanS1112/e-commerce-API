from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base    
from app.models.timestamp_mixin import TimestampMixin

class Cart(Base,TimestampMixin):
    __tablename__ = "carts"

    id:Mapped[int] = mapped_column(primary_key=True)
    user_id:Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    user = relationship("User", back_populates="cart")
    items = relationship("CartItems",cascade="all, delete-orphan", back_populates="cart")
