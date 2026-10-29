
from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_permission import UserPermission


db = SessionLocal()

try:
    # Find Super Admin role
    role = db.query(Role).filter(
        Role.name == "super admin"
    ).first()

    if not role:
        raise ValueError("Super Admin role not found!")

    # Find Super Admin user
    user = db.query(User).filter(
        User.role_id == role.id
    ).first()

    if not user:
        raise ValueError("Super Admin user not found!")

    # Get all permissions
    permissions = db.query(Permission).filter(
        Permission.is_active == True
    ).all()

    # Get permissions already assigned to this user
    assigned_ids = {
        permission_id
        for (permission_id,) in db.query(
            UserPermission.permission_id
        ).filter(
            UserPermission.user_id == user.id
        ).all()
    }

    # Assign only missing permissions
    new_links = [
        UserPermission(
            user_id=user.id,
            permission_id=permission.id
        )
        for permission in permissions
        if permission.id not in assigned_ids
    ]

    db.add_all(new_links)
    db.commit()

    print(f"Super Admin: {user.email}")
    print(f"New permissions assigned: {len(new_links)}")
    print("Super Admin permissions updated successfully!")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    raise

finally:
    db.close()