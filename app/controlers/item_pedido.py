from sqlalchemy.orm import Session
from models import ItemPedido
from schemas import *


def create_item_pedido_db(db: Session, item_pedido: ItemPedidoCreate):
    db_item_pedido = ItemPedido(**item_pedido.dict())
    db.add(db_item_pedido)
    db.commit()
    db.refresh(db_item_pedido)
    return db_item_pedido

def get_item_pedidos(db: Session):
    return db.query(ItemPedido).all()

def get_item_pedido(db: Session, item_pedido_id: int):
    return db.query(ItemPedido).filter(ItemPedido.id == item_pedido_id).first()

def update_item_pedido_db(db: Session, item_pedido_id: int, item_pedido: ItemPedidoUpdate):
    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id == item_pedido_id).first()
    if db_item_pedido:
        for key, value in item_pedido.dict().items():
            setattr(db_item_pedido, key, value)
        db.commit()
        db.refresh(db_item_pedido)
    return db_item_pedido

def delete_item_pedido(db: Session, item_pedido_id: int):
    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id == item_pedido_id).first()
    if db_item_pedido:
        db.delete(db_item_pedido)
        db.commit()
    return db_item_pedido
