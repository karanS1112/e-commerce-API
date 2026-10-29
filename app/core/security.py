from pwdlib import PasswordHash
from datetime import timezone,timedelta,datetime
from app.core.config import settings
import jwt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from fastapi import Depends,HTTPException,status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
#rthis is return the hashed instance
password_hash = PasswordHash.recommended()
#covert the plain text to hash
def hash_password(password: str):
    return password_hash.hash(password)
#verify the  plain and hash pass 
def verify_password(plain_password:str, hashed_password:str):
    return password_hash.verify(plain_password,hashed_password)

#create the JWT token 
def create_access_token(data:dict):
    #copy the data from login API
    to_encode = data.copy()
    # Set the. expire time 
    expire_time = datetime.now(timezone.utc) + timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Update the  expire time 
    to_encode.update({"exp":expire_time, "type": "access",})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
       algorithm= settings.JWT_ALGORITHM
    )

def get_current_user(token:str = Depends(oauth2_scheme),db:Session = Depends(get_db)):

    # HTTPException  variable create  here bcz it use below many condition so i have craeted  common
    credentials_exception =  HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid or expire token",
        headers= {"WWW-Authenticate": "Bearer"}
    )
    try:
        # it verify the token signature and  algorithm= hs256
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM])
        #it get user id
        user_id = payload.get('sub')
        #get Type token 
        token_type = payload.get("type")

        if token_type != "access":
            raise credentials_exception
        
        if user_id is None:
            raise credentials_exception
        
        if not isinstance(user_id, str) or not user_id.isdigit():
         raise credentials_exception
        
    except (jwt.InvalidTokenError,TypeError):
        raise credentials_exception
    # get user object
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:

        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN,detail="User account is not active")
    

    return user

def create_refresh_token(data:dict):
    #  This is copy the user data
     to_encode = data.copy() 
    #   expiry time set
     expire_time = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    #update the  expoiry time
     to_encode.update({"exp":expire_time,"type": "refresh",})
    #jwt.encode refresh roken genrate
     return jwt.encode(
         to_encode,
         settings.JWT_SECRET_KEY,
         algorithm=settings.JWT_ALGORITHM
     )


