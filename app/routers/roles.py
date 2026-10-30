from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.role import Role
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)

@router.get("/")
def get_all_router(db:Session = Depends(get_db), current_user=Depends(require_permission("role_read"))):
     roles = db.query(Role).all()

     return {
         "message": "Roles fetch successfully",
         "data":[{
             "id":role.id,
             "name":role.name,
             "is_active":role.is_active
         }
          for role in roles
         ]
        
     }

@router.post("/")
def create_role(name: str,is_active: bool = True, db: Session = Depends(get_db), current_user=Depends(require_permission("role_create"))):
    # Here i am checking the  exsisting role
    existing_role = db.query(Role).filter(
        Role.name == name
    ).first()
    # here i put the condition if exsisting role then show error
    if existing_role:
        raise HTTPException(
            status_code=409,
            detail="Role already exists"
        )
    #create new  role object
    role = Role(name=name,is_active=is_active)
    # add the role
    db.add(role)
    #save the role in db
    db.commit()
    # get the latest value form db
    db.refresh(role)

    return {
        "message": "Role created successfully",
        "data": {
            "id": role.id,
            "name": role.name,
            "is_active": role.is_active
        }
    }




@router.put("/{role_id}")
def update_role(role_id: int,is_active: Optional[bool] = None,name: Optional[str] = None, db: Session = Depends(get_db), _: User = Depends(require_permission("role_update"))
):
    # Find role using ID
    role = db.query(Role).filter(Role.id == role_id).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Prevent Super Admin deactivation
    if role.name.strip().lower() == "super admin" and is_active is False:
        raise HTTPException(
            status_code=403,
            detail="Super Admin cannot be deactivated"
        )

    # Check duplicate name
    if name is not None:
        name = name.strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Role name cannot be empty"
            )

        existing_role = db.query(Role).filter(
            Role.name.ilike(name),
            Role.id != role_id
        ).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role name already exists"
            )

        role.name = name

    # Update status
    if is_active is not None:
        role.is_active = is_active

    db.commit()
    db.refresh(role)

    return {
        "message": "Role updated successfully",
        "data": {
            "id": role.id,
            "name": role.name,
            "is_active": role.is_active
        }
    }