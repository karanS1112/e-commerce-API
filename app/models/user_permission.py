from sqlalchemy import String,Boolean,Integer,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User


class UserPermission(Base):
    __tablename__ = "user_permissions"

    user_id:Mapped[int] = mapped_column(
        ForeignKey("users.id",ondelete="CASCADE"),
        primary_key=True
    )
    permission_id:Mapped[int]= mapped_column(
        ForeignKey("permissions.id",ondelete="CASCADE"),
        primary_key=True
    )

    user: Mapped['User'] = relationship(
        back_populates= "user_permission_links"
    )
    permission: Mapped["Permission"] = relationship(
            back_populates="user_permission_links"
    )

