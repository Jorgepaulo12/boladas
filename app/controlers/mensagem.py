from sqlalchemy.orm import Session
from models import Mensage
from schemas import MensagemCreate, MensagemUpdate,U

def create_mensagem_db(db: Session, mensagem: MensagemCreate):
    db_mensagem = Mensagem(**mensagem.dict())
    db.add(db_mensagem)
    db.commit()
    db.refresh(db_mensagem)
    return db_mensagem

def get_mensagens(db: Session):
    return db.query(Mensagem).all()

def get_mensagem(db: Session, mensagem_id: int):
    return db.query(Mensagem).filter(Mensagem.id == mensagem_id).first()


def get_conversas_entre_usuarios(db: Session, usuario1_id: int, usuario2_id: int):
    return db.query(Mensagem).filter(
        (Mensagem.remetenteID == usuario1_id) & (Mensagem.destinatarioID == usuario2_id) |
        (Mensagem.remetenteID == usuario2_id) & (Mensagem.destinatarioID == usuario1_id)
    ).all()


def update_mensagem_db(db: Session, mensagem_id: int, mensagem: MensagemUpdate):
    db_mensagem = db.query(Mensagem).filter(Mensagem.id == mensagem_id).first()
    if db_mensagem:
        for key, value in mensagem.dict().items():
            setattr(db_mensagem, key, value)
        db.commit()
        db.refresh(db_mensagem)
    return db_mensagem

def delete_mensagem(db: Session, mensagem_id: int):
    db_mensagem = db.query(Mensagem).filter(Mensagem.id == mensagem_id).first()
    if db_mensagem:
        db.delete(db_mensagem)
        db.commit()
    return db_mensagem
