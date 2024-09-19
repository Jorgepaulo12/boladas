from sqlalchemy.orm import Session
from models import Usuario,InfoUsuario
from schemas import UsuarioCreate, UsuarioUpdate
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

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


def send_email(recipient: str, subject: str, body: str):
    sender_email = "jorgepaulomepia@gmail.com"  # Seu e-mail
    sender_password = "ryyuofxscbisgrre"  # Sua senha do e-mail

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Altere para o servidor SMTP do seu e-mail
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False



def gerar_senha_temporaria(length: int = 8) -> str:
    """Gera uma senha temporária aleatória."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(length))

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