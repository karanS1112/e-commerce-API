from sqlalchemy import String,Integer,Boolean,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.role import Role

class RolePermission(Base):
    __tablename__ = "role_permissions"
# Cascade usage:
# For example, if a role is deleted, the database automatically removes its related rows from the role_permissions table, but not from the permissions table.

    role_id:Mapped[int] = mapped_column(
            ForeignKey("roles.id",ondelete="CASCADE"),
            primary_key=True

    )
    permission_id:Mapped[int] = mapped_column(
        ForeignKey("permissions.id",ondelete="CASCADE"),
                    primary_key=True
    )

    role: Mapped["Role"] = relationship(
        back_populates="role_permission_links"
    )

    permission: Mapped["Permission"] = relationship(
        back_populates="permission_role_links"
    )