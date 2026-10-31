from fastapi import APIRouter, Depends, Form,HTTPException,status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, ValidationError
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from typing import Annotated
from app.core.security import (hash_password, verify_password,create_access_token,create_refresh_token)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.security import get_current_user
import jwt
from app.models.refresh_token import RefreshToken

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

class RefreshTokenRequest(BaseModel):
    refresh_token:str

class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    token_expiry: datetime   

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED
)
def register_user(
    first_name: str = Form(...),
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


@router.post("/login", response_model=TokenResponse)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(User).filter(
        func.lower(User.email) == form_data.username.lower()
    ).first()

    # Check email and password
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate access and refresh tokens
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    # Calculate token expiry
    token_expiry = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    refresh_expiry = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    try:
        # Check existing refresh token
        db_refresh_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).with_for_update().first()

        if db_refresh_token:
            db_refresh_token.token = refresh_token
            db_refresh_token.expires_at = refresh_expiry
            db_refresh_token.is_revoked = False

        else:
            db_refresh_token = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expires_at=refresh_expiry,
                is_revoked=False
            )
            db.add(db_refresh_token)

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save login session"
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "token_expiry": token_expiry
    }



@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token( request: RefreshTokenRequest, db: Session = Depends(get_db)):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token"
    )

    # decode and validate refresh token
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        # checking the type of token
        if (
            payload.get("type") != "refresh"
            or not isinstance(user_id, str)
            or not user_id.isdigit()
        ):
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, AttributeError):
        raise credentials_exception

    try:
        # Find the matching refresh token and lock its database row
        user_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.token == request.refresh_token
        ).with_for_update().first()

        if not user_token or user_token.is_revoked:
            raise credentials_exception

        # check refresh token expiry in the database
        if user_token.expires_at <= datetime.now(timezone.utc):
            raise credentials_exception

        # check user account
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user or not user.is_active:
            raise credentials_exception

        # generate new tokens
        new_access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        # calculate new expiry times
        token_expiry = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        refresh_expiry = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # replace old refresh token with the new one
        user_token.token = new_refresh_token
        user_token.expires_at = refresh_expiry
        user_token.is_revoked = False

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update refresh token"
        )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "token_expiry": token_expiry
    }

@router.post("/logout")
def logout_user(request: RefreshTokenRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Find the refresh token belonging to the currently logged-in user
    db_refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token,
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked.is_(False)
    ).first()

    # Check whether the refresh token exists and is active
    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or already revoked refresh token"
        )

    # Revoke the refresh token so it cannot be used again
    db_refresh_token.is_revoked = True

    # Save the logout changes in the database
    db.commit()

    # Return logout success message
    return {
        "message": "User logged out successfully"
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
