from fastapi import HTTPException,Depends,APIRouter,status
from app.models.user import User
from app.models.permission import Permission
from app.models.user_permission import UserPermission
from app.db.session import SessionLocal,sessionmaker,get_db
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.core.permissions import require_permission



router = APIRouter(
    prefix="/users",
    tags= ['User permission']
)

class UserPermissionAssign(BaseModel):
    permission_id:int = Field(gt=0)


@router.post("/{user_id}/permission",status_code=status.HTTP_201_CREATED)
def assign_permission(user_id:int,request:UserPermissionAssign, db: Session = Depends(get_db), current_user: User = Depends(require_permission('permission_assign')) ) :

    # get user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    #  get the active permisison
    permission = db.query(Permission).filter(Permission.id == request.permission_id, Permission.is_active == True).first()

    if not permission:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Permission is not found."
        )

    # exsisting permission check is it given or not 
    exsisting = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.permission_id == permission.id).first()

    if exsisting:
        raise HTTPException(
           detail= "Permission already given"
        )

    #assign the permission
    try:
        user_permission = UserPermission(
            user_id = user_id,
            permission_id = permission.id
        )
        #add into db
        db.add(user_permission)

        #save the permission
        db.commit()
    except HTTPException:
        db.rollback
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "Unable to assign the permission"
        )
    return{
        "message": "Permission assign sucessfully",
        "data":{
            "user_id":user_id,
            "permission_id": permission.id,
            "permission_name": permission.name
        }
    }


    

@router.get("/{user_id}/permissions")
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("permission_view")
    )
):
    # 1. Check whether user exists
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 2. Get user's assigned permissions
    permissions = db.query(Permission).join(
        UserPermission,
        UserPermission.permission_id == Permission.id
    ).filter(
        UserPermission.user_id == user_id
    ).all()

    # 3. Return response
    return {
        "message": "User permissions fetched successfully",
        "user_name": f"{current_user.first_name} {current_user.last_name}",
        "data": [
            {
                "id": permission.id,
                "name": permission.name,
                "is_active": permission.is_active
            }
            for permission in permissions
        ]
    }

    
@router.delete("/{user_id}/permission/{permission_id}")
def remove_permission(user_id: int,permission_id: int,db: Session = Depends(get_db),current_user: User = Depends(
        require_permission("permission_assign")
    )
):
    # 1. Check user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 2. Check assigned permission
    user_permission = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.permission_id == permission_id
    ).first()

    if not user_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission is not assigned to this user"
        )

    # 3. Remove permission
    try:
        db.delete(user_permission)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to remove permission"
        )

    return {
        "message": "Permission removed successfully",
        "data": {
            "user_id": user_id,
            "permission_id": permission_id
        }
    }




