from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import Usuario, Admin  # Adicione a importação da classe Admin
from schemas import UsuarioCreate,AdminCreate,AdminBase
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

# Função para criar o token JWT com o ID do usuário e o papel
def create_access_token(data: dict, role: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode.update({"role": role})  # Adiciona o papel ao token
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para buscar um usuário pelo ID
def get_user(db: Session, user_id: int):
    return db.query(Usuario).filter(Usuario.id == user_id).first()

# Função para buscar um administrador pelo ID
def get_admin(db: Session, admin_id: int):
    return db.query(Admin).filter(Admin.id == admin_id).first()

# Função para autenticar o usuário
# Função para autenticar o usuário
def authenticate_user(db: Session, username: str, password: str):
    # Busca o usuário pelo username
    user = db.query(Usuario).filter(Usuario.username == username).first()

    # Verifica se o usuário existe e se a senha é válida
    if not user or not verify_password(password, user.senha):
        return False

    # Verifica se o campo 'ativo' está como True
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado, por favor contate o administrador."
        )

    return user

# Função para autenticar o administrador
def authenticate_admin(db: Session, email: str, password: str):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin or not verify_password(password, admin.senha):
        return False
    return admin

# Função para obter o usuário atual
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

# Função para obter o administrador atual
def get_current_admin(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "admin":
            raise credentials_exception  # Se o papel não for admin, acesso negado
        admin_id: int = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = get_admin(db, admin_id=admin_id)
    if admin is None:
        raise credentials_exception
    return admin

# Função para registrar um novo usuário (hashing da senha)
def register_user(db: Session, user: UsuarioCreate):
    hashed_password = get_password_hash(user.senha)
    db_user = Usuario(
        username=user.username,
        email=user.email,
        tipo=user.tipo,
        senha=hashed_password,  # Senha pode ser None para usuários do Google
        nome=user.username,  # Nome ou apelido do usuário
        saldo=0.0,  # Saldo inicial do usuário
      # Adicione outros campos conforme necessário
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


    # Função para registrar um novo administrador (hashing da senha)
def register_admin(db: Session, admin: AdminCreate):
    hashed_password = get_password_hash(admin.senha)
    db_admin = Admin(
        nome=admin.nome,  # Use o nome fornecido
        email=admin.email,
        senha=hashed_password  # A senha deve ser hashada
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin
