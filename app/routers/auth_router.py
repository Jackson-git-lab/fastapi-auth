# route/auth_router.py
from fastapi import APIRouter, Body, Depends, HTTPException
from app.classes import UserValidation, Token, TokenRefresh, UserResponse
from app.models import Users, RefreshToken
from app.database import get_db  
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from sqlalchemy import or_
from sqlalchemy.orm import Session 

router = APIRouter(
    tags=["auth"],
    prefix="/auth"
)

#  HTTPBearer
security = HTTPBearer()

# bcrypt config
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#jwt config
#key generer avec cette commande : openssl rand -hex 64
JWT_SECRET_KEY = "faf3e271648d65ce8ce17d8656b439e03bc6aac732aea857f9906f11d6170fc4fc909c883d7c1bffe1517d5a5ce7ffceb940b5e5ed540d8157bda31985dc355d"
JWT_ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# function pour login
def authenticate_user(username_or_email: str, password: str, db):
    user = db.query(Users).filter(
        or_(Users.username == username_or_email, Users.email == username_or_email)
    ).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp(), "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGO)

def create_refresh_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire.timestamp(), "type": "refresh"})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGO)
    return token, expire

# function pour auth middleware 
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)], 
    db: Session = Depends(get_db)
):
    token = credentials.credentials  
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGO])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        token_type: str = payload.get("type")
        
        if username is None or user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

# nos endpoints 

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    db: Annotated[Session, Depends(get_db)],  
    user_body: UserValidation = Body()
):
    existing_user = db.query(Users).filter(
        (Users.username == user_body.username) | (Users.email == user_body.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username ou email déjà utilisé"
        )
    
    new_user = Users(
        email=user_body.email,
        username=user_body.username,
        first_name=user_body.first_name,
        last_name=user_body.last_name,
        hashed_password=bcrypt_context.hash(user_body.password),
        is_active=True,
        role=user_body.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
async def login_user(
    db: Annotated[Session, Depends(get_db)],  
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte désactivé"
        )
    
    access_token = create_access_token({"sub": user.username, "id": user.id})
    refresh_token, expires_at = create_refresh_token({"sub": user.username, "id": user.id})
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: Annotated[Session, Depends(get_db)],  
    token_data: TokenRefresh
):
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGO]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré"
            )
        
        user = db.query(Users).filter(Users.id == db_token.user_id).first()
        new_access_token = create_access_token({"sub": user.username, "id": user.id})
        
        return {
            "access_token": new_access_token,
            "refresh_token": token_data.refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

@router.post("/logout")
async def logout(
    db: Annotated[Session, Depends(get_db)],  
    token_data: TokenRefresh
):
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_data.refresh_token
    ).first()
    
    if db_token:
        db_token.is_active = False
        db.commit()
    
    return {"message": "Déconnexion réussie"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Users = Depends(get_current_user)):
    return current_user