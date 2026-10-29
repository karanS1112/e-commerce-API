
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.role import Role
from app.models.permission import Permission


# Router ko endpoints se pehle define karna zaroori hai
router = APIRouter(
    prefix="/role-permissions",
    tags=["Role Permissions"]
)


# Get active roles and permissions ki list
@router.get("/options")
def get_role_permission_options(
    db: Session = Depends(get_db)
):
    roles = db.query(Role).filter(
        Role.is_active == True
    ).all()

    permissions = db.query(Permission).filter(
        Permission.is_active == True
    ).all()

    return {
        "message": "Roles and permissions fetched successfully",
        "data": {
            "roles": [
                {"id": role.id, "name": role.name}
                for role in roles
            ],
            "permissions": [
                {"id": permission.id, "name": permission.name}
                for permission in permissions
            ]
        }
    }
