from sqlalchemy.orm import Session
from models import Pedido, Produto, Notificacao
from schemas import PedidoCreate, PedidoUpdate
from fastapi import HTTPException


def create_pedido_db(db: Session, pedido: PedidoCreate):
    # Verifica se o produto existe
    produto = db.query(Produto).filter(Produto.id == pedido.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Calcula o preço total do pedido
    preco_total = pedido.quantidade * produto.preco
    
    # Cria o pedido
    db_pedido = Pedido(
        CustomerID=pedido.CustomerID,
        produto_id=pedido.produto_id,
        quantidade=pedido.quantidade,
        preco_unitario=produto.preco,
        preco_total=preco_total,
        status=pedido.status
    )
    
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)

    # Envia notificação ao vendedor
    enviar_notificacao(db, produto.CustomerID, f"Você recebeu um novo pedido para o produto {produto.nome}!")

    return db_pedido

def listar_notificacoes(db: Session, usuario_id: int):
    notificacoes = db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id).all()
    return notificacoes

def get_pedidos(db: Session):
    return db.query(Pedido).all()


def get_pedido(db: Session, pedido_id: int):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return pedido


def get_pedidos_recebidos(db: Session, user_id: int):
    """
    Pega os pedidos recebidos para os produtos de um usuário específico (vendedor).
    Args:
        db (Session): Sessão do banco de dados.
        user_id (int): ID do usuário (vendedor).

    Returns:
        List[Pedido]: Lista de pedidos para os produtos do usuário.
    """
    pedidos_recebidos = db.query(Pedido).join(Produto).filter(Produto.CustomerID == user_id).all()
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
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    # Atualiza os campos do pedido
    for key, value in pedido.dict().items():
        setattr(db_pedido, key, value)
    
    db.commit()
    db.refresh(db_pedido)
    return db_pedido


def delete_pedido(db: Session, pedido_id: int):
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    db.delete(db_pedido)
    db.commit()
    return db_pedido


def enviar_notificacao(db: Session, usuario_id: int, mensagem: str):
    """
    Função para enviar notificações para o usuário.
    Args:
        db (Session): Sessão do banco de dados.
        usuario_id (int): ID do usuário que receberá a notificação.
        mensagem (str): Mensagem da notificação.
    
    Returns:
        Notificação criada.
    """
    notificacao = Notificacao(
        usuario_id=usuario_id,
        mensagem=mensagem
    )
    db.add(notificacao)
    db.commit()
    db.refresh(notificacao)
    return notificacao
