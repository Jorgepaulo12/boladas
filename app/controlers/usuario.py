from sqlalchemy.orm import Session
from models import Usuario,InfoUsuario
from schemas import UsuarioCreate, UsuarioUpdate

def create_usuario_db(db: Session, usuario: UsuarioCreate):
    db_usuario = Usuario(**usuario.dict())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuarios(db: Session):
    return db.query(Usuario).all()

def get_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def update_usuario_db(db: Session, usuario_id: int, usuario: UsuarioUpdate):
    # Certifique-se de usar o nome correto da coluna no modelo SQLAlchemy
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario:
        for key, value in usuario.dict().items():
            setattr(db_usuario, key, value)
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def delete_usuario_db(db: Session, usuario_id: int):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
    return db_usuario

def get_perfil(db: Session, usuario_id: int):
    # Atualiza a consulta para fazer join entre Usuario e InfoUsuario
    usuario_info = db.query(Usuario, InfoUsuario).join(InfoUsuario, Usuario.id == InfoUsuario.id).filter(Usuario.id == usuario_id).first()
    
    if usuario_info:
        usuario, info_usuario = usuario_info
        return {
            "username": usuario.username,
            "nome": usuario.nome,
            "perfil": info_usuario.perfil
        }
    return None