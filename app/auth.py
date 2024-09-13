from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database import SessionLocal
from models import Usuario
from schemas import UsuarioCreate

# Configurações do JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema para OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    """Retrieve a user by username from the database."""
    return db.query(Usuario).filter(Usuario.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user by verifying username and password."""
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.senha):
        return False
    return user

def get_current_user(db: Session = Depends(SessionLocal), token: str = Depends(oauth2_scheme)):
    """Get the current authenticated user based on the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def register_user(db: Session, user: UsuarioCreate):
    """Register a new user by hashing their password and saving them to the database."""
    hashed_password = get_password_hash(user.senha)
    db_user = Usuario(
        username=user.username,
        email=user.email,
        senha=hashed_password,
        nome=user.username,  # Adicione outros campos conforme necessário
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
