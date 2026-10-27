from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.role import Role

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)

@router.get("/")
def get_all_router(db:Session = Depends(get_db)):
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
def create_role(name: str,is_active: bool = True, db: Session = Depends(get_db)):
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


from typing import Optional

@router.put("/{role_id}")
def update_role( role_id: int,is_active:bool,name: Optional[str] = None,db: Session = Depends(get_db)
):
    # Find role using ID
    role = db.query(Role).filter(
        Role.id == role_id
    ).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Check duplicate name only if a new name is provided
    if name is not None:
        existing_role = db.query(Role).filter(
            Role.name == name,
            Role.id != role_id
        ).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role name already exists"
            )

        role.name = name

    # Update status only if provided
    if is_active is not None:
        role.is_active = is_active

    db.commit()
    db.refresh(role)

    if is_active is False:
        message = "Role deactivated successfully"
    elif is_active is True:
        message = "Role activated successfully"
    elif name is not None:
        message = "Role name updated successfully"
    else:
        message = "No changes provided"

    if role.name.lower() == "super admin" and is_active is False:
        raise HTTPException(
            status_code=403,
            detail="Super Admin cannot be deactivated"
        )    

    return {
        "message": message,
        "data": {
            "id": role.id,
            "name": role.name,
            "is_active": role.is_active
        }
    }
