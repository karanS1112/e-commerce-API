from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.permission import Permission


router = APIRouter(
    prefix='/permission',
    tags=["Permission"]
)


@router.post("/")
def create_permission(name: str,db: Session = Depends(get_db)
):
    # Check whether permission already exists
    existing_permission = db.query(Permission).filter(
        Permission.name == name
    ).first()

    if existing_permission:
        raise HTTPException(
            status_code=409,
            detail="Permission already exists"
        )

    # Create new permission
    permission = Permission(name=name)

    db.add(permission)
    db.commit()
    db.refresh(permission)

    return {
        "message": "Permission created successfully",
        "data": {
            "id": permission.id,
            "name": permission.name,
            "is_active": permission.is_active
        }
    }


@router.get("/")
def get_all_permissions(
    db: Session = Depends(get_db)
):
    permissions = db.query(Permission).all()

    return {
        "message": "Permissions fetched successfully",
        "data": [
            {
                "id": permission.id,
                "name": permission.name,
                "is_active": permission.is_active
            }
            for permission in permissions
        ]
    }

