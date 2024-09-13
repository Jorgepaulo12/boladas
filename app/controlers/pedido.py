from sqlalchemy.orm import Session
from models import Pedido,ItemPedido,Produto
from schemas import PedidoCreate, PedidoUpdate
from fastapi import HTTPException

def create_pedido_db(db: Session, pedido: PedidoCreate):
    db_pedido = Pedido(**pedido.dict())
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

def get_pedidos(db: Session):
    return db.query(Pedido).all()

def get_pedido(db: Session, pedido_id: int):
    return db.query(Pedido).filter(Pedido.id  == pedido_id).first()









def get_pedidos_recebidos(db: Session, user_id: int):
    """
    Pega os pedidos recebidos para os produtos de um usuário específico.
    Args:
        db (Session): Sessão do banco de dados.
        user_id (int): ID do usuário (vendedor).

    Returns:
        List[Pedido]: Lista de pedidos para os produtos do usuário.
    """
    pedidos_recebidos = db.query(Pedido).join(ItemPedido).join(Produto).filter(Produto.CustomerID == user_id).all()
    if not pedidos_recebidos:
        raise HTTPException(status_code=404, detail="Nenhum pedido recebido encontrado para este usuário.")
    return pedidos_recebidos





def get_pedidos_feitos(db: Session, user_id: int):
    """
    Pega os pedidos feitos por um usuário específico (cliente).
    Args:
        db (Session): Sessão do banco de dados.
        user_id (int): ID do usuário (cliente).

    Returns:
        List[Pedido]: Lista de pedidos feitos pelo usuário.
    """
    pedidos_feitos = db.query(Pedido).filter(Pedido.CustomerID == user_id).all()
    if not pedidos_feitos:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado para este usuário.")
    return pedidos_feitos





def update_pedido_db(db: Session, pedido_id: int, pedido: PedidoUpdate):
    db_pedido = db.query(Pedido).filter(Pedido.id  == pedido_id).first()
    if db_pedido:
        for key, value in pedido.dict().items():
            setattr(db_pedido, key, value)
        db.commit()
        db.refresh(db_pedido)
    return db_pedido

def delete_pedido(db: Session, pedido_id: int):
    db_pedido = db.query(Pedido).filter(Pedido.id  == pedido_id).first()
    if db_pedido:
        db.delete(db_pedido)
        db.commit()
    return db_pedido
