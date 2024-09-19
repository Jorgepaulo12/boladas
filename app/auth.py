from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import Usuario
from schemas import UsuarioCreate
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configurações do JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema para OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Função para gerar um hash da senha
def hash_password(password):
    return pwd_context.hash(password)



# Funções de hash e verificação de senha
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Função para criar o token JWT com o ID do usuário
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para buscar um usuário pelo ID
def get_user(db: Session, user_id: int):
    return db.query(Usuario).filter(Usuario.id == user_id).first()

# Função para autenticar o usuário usando o ID
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user or not verify_password(password, user.senha):
        return False
    return user

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user


# Função para registrar um novo usuário (hashing da senha)
def register_user(db: Session, user: UsuarioCreate):
    hashed_password = get_password_hash(user.senha)
    db_user = Usuario(
        username=user.username,
        email=user.email,
        tipo=user.tipo,
        senha=hashed_password,
        nome=user.username,  # Adicione outros campos conforme necessário
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user