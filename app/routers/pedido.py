from controlers.pedido import *
from schemas import *
from auth import *
from fastapi import APIRouter,Form

router=APIRouter(prefix="/pedidos",tags=["rotas de pedido"])


@router.post("/{pedido_id}/aceitar/")
def aceitar_pedido_route(pedido_id: int, vendedor_id: int, db: Session = Depends(get_db)):
    return aceitar_pedido(db, pedido_id, vendedor_id)

@router.post("/{pedido_id}/confirmar-recebimento/")
def confirmar_recebimento_route(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    return confirmar_recebimento_cliente(db, pedido_id, cliente_id)

@router.post("/{pedido_id}/confirmar-pagamento/")
def confirmar_pagamento_route(pedido_id: int, vendedor_id: int, db: Session = Depends(get_db)):
    return confirmar_pagamento_vendedor(db, pedido_id, vendedor_id)


@router.delete("/pedidos/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido =delete_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@router.delete("/item_pedidos/{item_pedido_id}")
def delete_item_pedido(item_pedido_id: int, db: Session = Depends(get_db)):
    db_item_pedido = delete_item_pedido(db=db, item_pedido_id=item_pedido_id)
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return db_item_pedido

@router.put("/pedidos/{pedido_id}")
def update_pedido(pedido_id: int, pedido: PedidoUpdate, db: Session = Depends(get_db)):
    db_pedido = update_pedido(db=db, pedido_id=pedido_id, pedido=pedido)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

# Rota para pegar os pedidos recebidos por um usuário específico
@router.get("/recebidos/{user_id}")
def pedidos_recebidos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_recebidos(db, user_id)

# Rota para pegar os pedidos feitos por um usuário específico
@router.get("/feitos/{user_id}")
def pedidos_feitos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_feitos(db, user_id)

@router.get("/{pedido_id}")
def read_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido = get_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@router.post("/")
def create_pedido(
    CustomerID: int = Form(...),
    produto_id: int = Form(...),
    quantidade: int = Form(...),
    status: str = Form(default="Pendente"),
    db: Session = Depends(get_db),
    mensagem: str = None,
):
    # Cria o pedido usando a função existente no controlador
    pedido_data = PedidoCreate(
        CustomerID=CustomerID,
        produto_id=produto_id,
        quantidade=quantidade,
        status=status,
        mensagem=mensagem
    )
    
    # Salva o pedido e retorna o pedido criado
    pedido_criado = create_pedido_db(db=db, pedido=pedido_data,mensagem=mensagem)

    return {"mensagem": "Pedido criado com sucesso.", "pedido_id": pedido_criado.id}

