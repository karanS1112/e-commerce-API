from sqlalchemy import String,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.role_permission import RolePermission

class Permission(Base):
    __tablename__ = "permissions"

    id:Mapped[int] = mapped_column(
        primary_key=True
    )
    name:Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    permission_role_links: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission"
    )