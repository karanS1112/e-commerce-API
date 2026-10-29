
from fastapi import APIRouter, Depends, Form,HTTPException,status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, ValidationError
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from typing import Annotated
from app.core.security import (hash_password, verify_password,create_access_token,hash_password,create_refresh_token)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.security import get_current_user
import jwt


# Pydantic model for request validation
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


# Response model
class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role_id: int
    role_name: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type: str
    token_expiry:datetime    

class RefreshToken(BaseModel):
    refresh_token:str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    token_expiry: datetime   

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED
)
def register_user(
    first_name: str = Form(example="Enter First Name"),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form( json_schema_extra={"format": "password"}),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    postal_code: str | None = Form(None),
    country: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # Validate request data using Pydantic
    try:
        user_data = UserRegister(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    # Check if email already exists
    existing_user = (
        db.query(User)
        .filter(
            func.lower(User.email) == str(user_data.email).lower()
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Find active customer role
    customer_role = (
        db.query(Role)
        .filter(
            func.lower(Role.name) == "customer",
            Role.is_active.is_(True)
        )
        .first()
    )

    if not customer_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer role not found"
        )

    # Create user
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=str(user_data.email),
        password=hash_password(user_data.password),
        phone=user_data.phone,
        address=user_data.address,
        city=user_data.city,
        state=user_data.state,
        postal_code=user_data.postal_code,
        country=user_data.country,
        role_id=customer_role.id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=new_user.email,
        role_id=new_user.role_id,
        role_name=customer_role.name,
        is_active=new_user.is_active,
    )

@router.post("/login",response_model = TokenResponse)

def login_user(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db:Session = Depends(get_db)):

    #find the user email
    user = db.query(User).filter(func.lower(User.email) == form_data.username.lower()).first()

    # Error  message show if user email and password not match
    if  not user or not verify_password(form_data.password,user.password):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,detail="Inavalid emain or passowrd")
    
# here is. checking. user is active. or not
    if not user.is_active:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= "User account is inactive"
        )
    
    # create the access toke here  which build security file 
    access_token = create_access_token(data={"sub":str(user.id)})
    refresh_token = create_refresh_token(data={"sub":str(user.id)})

    token_expiry = datetime.now(timezone.utc) + timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": access_token,
        "refresh_token":refresh_token,
        "token_type": "bearer",
        "token_expiry": token_expiry,

    }

@router.post("/refresh",response_model=AccessTokenResponse
)
def refresh_access_token(request: RefreshToken,db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if not isinstance(payload, dict):
            raise credentials_exception

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "refresh":
            raise credentials_exception

        if not isinstance(user_id, str) or not user_id.isdigit():
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user or not user.is_active:
        raise credentials_exception

    new_access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    token_expiry = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "token_expiry": token_expiry,
    }

@router.get("/verify", response_model=UserResponse)
#verify the bearer token 
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = db.query(Role).filter(
        Role.id == current_user.role_id
    ).first()

    return UserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        role_id=current_user.role_id,
        role_name=role.name if role else "",
        is_active=current_user.is_active,
    )
