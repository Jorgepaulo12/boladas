import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, File

from models import InfoUsuario
from schemas import InfoUsuarioCreate, InfoUsuarioUpdate

# Definindo caminhos de upload
PROFILE_UPLOAD_DIR = "uploads/perfil"
DOCUMENT_UPLOAD_DIR = "uploads/documentos"

# Criando diretórios se não existirem
os.makedirs(PROFILE_UPLOAD_DIR, exist_ok=True)
os.makedirs(DOCUMENT_UPLOAD_DIR, exist_ok=True)

def save_image(file: UploadFile, upload_dir: str) -> str:
    """
    Salva uma imagem no diretório especificado.

    Args:
        file (UploadFile): Arquivo da imagem enviada pelo usuário.
        upload_dir (str): Diretório onde a imagem será armazenada.

    Returns:
        str: Nome único do arquivo salvo.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado não é uma imagem.")

    # Gerando um nome de arquivo único
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Salvando a imagem no diretório apropriado
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return unique_filename

def create_info_usuario_db(db: Session, info_usuario: InfoUsuarioCreate):
    """
    Cria uma nova entrada de InfoUsuario no banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario (InfoUsuarioCreate): Dados do usuário.

    Returns:
        InfoUsuario: Instância do InfoUsuario criada.
    """
    db_info_usuario = InfoUsuario(**info_usuario.dict())
    db.add(db_info_usuario)
    db.commit()
    db.refresh(db_info_usuario)
    return db_info_usuario

def get_info_usuarios(db: Session):
    """
    Recupera todas as entradas de InfoUsuario no banco de dados.

    Args:
        db (Session): Sessão do banco de dados.

    Returns:
        List[InfoUsuario]: Lista de instâncias InfoUsuario.
    """
    return db.query(InfoUsuario).all()

def get_info_usuario(db: Session, info_usuario_id: int):
    """
    Recupera uma entrada de InfoUsuario pelo ID.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario_id (int): ID do InfoUsuario.

    Returns:
        InfoUsuario: Instância do InfoUsuario se encontrado, caso contrário None.
    """
    return db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()

def update_info_usuario_db(db: Session, info_usuario_id: int, info_usuario: InfoUsuarioUpdate):
    """
    Atualiza uma entrada existente de InfoUsuario no banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario_id (int): ID do InfoUsuario.
        info_usuario (InfoUsuarioUpdate): Novos dados para o InfoUsuario.

    Returns:
        InfoUsuario: Instância do InfoUsuario atualizada se encontrado, caso contrário None.
    """
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()
    if db_info_usuario:
        for key, value in info_usuario.dict().items():
            setattr(db_info_usuario, key, value)
        db.commit()
        db.refresh(db_info_usuario)
    return db_info_usuario

def update_info_usuario_profile_picture(db: Session, info_usuario_id: int, new_profile_picture: str):
    """
    Atualiza apenas a foto de perfil do usuário no banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario_id (int): ID do InfoUsuario.
        new_profile_picture (str): Nome do novo arquivo de foto de perfil.
    """
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()
    if db_info_usuario:
        db_info_usuario.perfil = new_profile_picture
        db.commit()
        db.refresh(db_info_usuario)
    else:
        raise HTTPException(status_code=404, detail="Informações do usuário não encontradas.")

def update_info_usuario_document_picture(db: Session, info_usuario_id: int, new_document_picture: str):
    """
    Atualiza apenas a foto de documento do usuário no banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario_id (int): ID do InfoUsuario.
        new_document_picture (str): Nome do novo arquivo de foto de documento.
    """
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()
    if db_info_usuario:
        db_info_usuario.foto_bi = new_document_picture
        db.commit()
        db.refresh(db_info_usuario)
    else:
        raise HTTPException(status_code=404, detail="Informações do usuário não encontradas.")

def delete_info_usuario(db: Session, info_usuario_id: int):
    """
    Remove uma entrada de InfoUsuario do banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        info_usuario_id (int): ID do InfoUsuario.

    Returns:
        InfoUsuario: Instância do InfoUsuario removido se encontrado, caso contrário None.
    """
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()
    if db_info_usuario:
        db.delete(db_info_usuario)
        db.commit()
    return db_info_usuario
