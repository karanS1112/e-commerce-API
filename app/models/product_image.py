from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.timestamp_mixin import TimestampMixin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.product import Product

class ProductImage(Base,TimestampMixin):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key= True)
    product_id:Mapped[int] = mapped_column(
        ForeignKey ("products.id", ondelete="CASCADE"),
        nullable=False,
        index= True
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    product: Mapped["Product"] = relationship(
        back_populates="images"
    )
