from getpass import getpass
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models import (User,Role)
from sqlalchemy import func


db = SessionLocal()

try:
    email = input("Email: ").strip().lower()
    password = getpass("password: ")
    # Find or create Super Admin role
    role = db.query(Role).filter(func.lower(Role.name)== "super admin").first()

    # role is not available we can create the. role here 
    if not role:
        role = Role(name="super admin", is_active=True)
        db.add(role)
        db.flush()

    #  get user
    user = db.query(User).filter(
        User.email == email
    ).first()  
    # if user. already exsist
    if user:
        print("User already exists!")
    else:
        user = User(
            first_name="Super",
            last_name="Admin",
            email=email,
            password=hash_password(password),
            role_id=role.id,
            is_active=True,
        )  
        db.add(user)
        db.commit()
        print("Super Admin created successfully!")

except Exception:
    db.rollback()
    raise

finally:
    db.close()