from sqlalchemy import String,Integer,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.role_permission import RolePermission

class Role(Base):
    __tablename__= "roles"

    id:Mapped[int] = mapped_column(
        primary_key = True
    )
    name:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    role_permission_links: Mapped[list["RolePermission"]] = relationship(
        back_populates="role"
    )