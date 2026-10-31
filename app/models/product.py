from sqlalchemy import String,Integer,Boolean,Text,Float,Numeric
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from app.models.timestamp_mixin import TimestampMixin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.product_image import ProductImage

class Product(Base,TimestampMixin):
    __tablename__ = "products"

    id:Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    name:Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )
    description:Mapped[Text] = mapped_column(
        Text,
        nullable= True
    )
    price:Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False
        
    )
    stock:Mapped[int] = mapped_column(
        Integer,
        default= 0,
        nullable= False
    )
    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    images:Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
    )