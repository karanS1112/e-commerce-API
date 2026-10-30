
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.post("/register-request", status_code=status.HTTP_201_CREATED)
def employee_register_request(
    first_name: str = Form(...),
    last_name: str |None = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    requested_role: str = Form(...),  # User selects role NAME
    db: Session = Depends(get_db)
):

    # Check duplicate email
    existing_user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Get selected role by NAME from database
    requested_role = db.query(Role).filter(
        Role.name.ilike(requested_role.strip()),
        Role.is_active.is_(True)
    ).first()

    if not requested_role:
        raise HTTPException(
            status_code=404,
            detail="Selected role not found or inactive"
        )

    # Prevent Customer and Super Admin registration requests
    if requested_role.name.lower() in ["customer", "super admin"]:
        raise HTTPException(
            status_code=400,
            detail="You cannot request this role"
        )

    # Get default Customer role
    customer_role = db.query(Role).filter(
        Role.name.ilike("customer"),
        Role.is_active.is_(True)
    ).first()

    if not customer_role:
        raise HTTPException(
            status_code=500,
            detail="Customer role not found"
        )

    # Create pending employee account
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email.strip().lower(),
        password=hash_password(password),
        role_id=customer_role.id,
        requested_role_id=requested_role.id,
        approval_status="pending",
        is_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registration request submitted successfully. Waiting for Super Admin approval.",
        "user_id": new_user.id,
        "requested_role": requested_role.name,
        "approval_status": new_user.approval_status
    }



@router.get("/pending-requests")
def get_pending_employee_requests(
    db: Session = Depends(get_db)
):
    pending_users = db.query(User).filter(
        User.approval_status == "pending"
    ).order_by(User.id.desc()).all()

    return {
        "message": "Pending employee requests fetched successfully",
        "total_requests": len(pending_users),
        "data": [
            {
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "current_role": user.role.name,
                "requested_role": user.requested_role.name,
                "approval_status": user.approval_status,
                "is_active": user.is_active
            }
            for user in pending_users
        ]
    }


@router.put("/update-request/{user_id}")
def update_employee_request(
    user_id: int,
    action: str = Form(...),  # approve or reject
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.approval_status != "pending":
        raise HTTPException(
            status_code=400,
            detail="This registration request is already approved"
        )

    if action.lower() == "approve":

        requested_role = db.query(Role).filter(
            Role.id == user.requested_role_id,
            Role.is_active.is_(True)
        ).first()

        if not requested_role:
            raise HTTPException(
                status_code=400,
                detail="Requested role is inactive or does not exist"
            )

        user.role_id = requested_role.id
        user.approval_status = "approved"
        user.is_active = True

    elif action.lower() == "reject":

        user.approval_status = "rejected"
        user.is_active = False

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Use approve or reject"
        )

    db.commit()
    db.refresh(user)

    return {
        "message": f"Employee request {action.lower()} successfully",
        "user_id": user.id,
        "approval_status": user.approval_status,
        "is_active": user.is_active
    }
