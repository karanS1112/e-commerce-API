from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.permission import Permission
from app.models.user_permission import UserPermission

#it  choose the permission
def require_permission(permission_name: str):

    # This function check the permission  of. current user  
    def check_permission(
        # it  check the current user details 
        user=Depends(get_current_user),
        # it provide the db session for help to check the permission 
        db: Session = Depends(get_db)
    ):
        #it provides user permission object  
        permission = db.query(UserPermission).join(
            Permission
        ).filter(
            UserPermission.user_id == user.id,
            Permission.name == permission_name,
            Permission.is_active == True
        ).first()

        if not permission:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        return user

    return check_permission