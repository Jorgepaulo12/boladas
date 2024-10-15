from sqlalchemy.orm import Session
from models import Pedido, Produto, Notificacao, Usuario, Wallet
from schemas import PedidoCreate, PedidoUpdate
from fastapi import HTTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from datetime import datetime

def send_email(recipient: str, subject: str, body: str):
    sender_email = "jorgepaulomepia@gmail.com"  # Seu e-mail
    sender_password = "ryyuofxscbisgrre"  # Sua senha de app (senha específica do Gmail)

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Servidor SMTP do Gmail
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

def enviar_notificacao(db: Session, usuario_id: int, mensagem: str):
    notificacao = Notificacao(
        usuario_id=usuario_id,
        mensagem=mensagem,
        data=datetime.utcnow()
    )
    db.add(notificacao)
    db.commit()
    db.refresh(notificacao)
    return notificacao

def create_pedido_db(db: Session, pedido: PedidoCreate):
    # Verifica se o produto existe
    produto = db.query(Produto).filter(Produto.id == pedido.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    # Verifica se a quantidade solicitada está disponível no estoque
    if produto.quantidade_estoque < pedido.quantidade:
        raise HTTPException(status_code=400, detail="Estoque insuficiente para o pedido.")

    # Calcula o preço total do pedido
    preco_total = pedido.quantidade * produto.preco

    # Congela o saldo do comprador
    wallet_comprador = db.query(Wallet).filter(Wallet.usuario_id == pedido.CustomerID).first()
    if not wallet_comprador or wallet_comprador.saldo_principal < preco_total:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    # Congela o saldo do comprador e atualiza o saldo congelado do vendedor
    wallet_comprador.saldo_congelado += preco_total
    wallet_comprador.saldo_principal -= preco_total

    # Cria o pedido
    db_pedido = Pedido(
        CustomerID=pedido.CustomerID,
        produto_id=pedido.produto_id,
        quantidade=pedido.quantidade,
        preco_unitario=produto.preco,
        preco_total=preco_total,
        status="Pendente"
    )

    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)

    # Busca o e-mail do vendedor (usuário que publicou o produto) na tabela 'usuarios'
    vendedor = db.query(Usuario).filter(Usuario.id == produto.CustomerID).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado.")

    vendedor_email = vendedor.email  # Pega o e-mail do vendedor
    produto_nome = produto.nome  # Pega o nome do produto

    # Envia o e-mail de notificação ao vendedor
    email_enviado = send_email(
        recipient=vendedor_email,
        subject="Novo Pedido Recebido",
        body=f"Você recebeu um novo pedido para o produto: {produto_nome}"
    )

    if not email_enviado:
        raise HTTPException(status_code=500, detail="Falha ao enviar o e-mail de notificação.")

    # Chama a função enviar_notificacao para criar a notificação
    try:
        mensagem = f"Você recebeu um novo pedido para o produto {produto_nome}"
        enviar_notificacao(db, vendedor.id, mensagem)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar notificação: {str(e)}")

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
    pedidos_recebidos = db.query(Pedido).join(Produto).filter(Produto.CustomerID == user_id).all()
    if not pedidos_recebidos:
        raise HTTPException(status_code=404, detail="Nenhum pedido recebido encontrado para este usuário.")
    return pedidos_recebidos

def get_pedidos_feitos(db: Session, user_id: int):
    pedidos_feitos = db.query(Pedido).filter(Pedido.CustomerID == user_id).all()
    if not pedidos_feitos:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado para este usuário.")
    return pedidos_feitos

def update_pedido_db(db: Session, pedido_id: int, pedido: PedidoUpdate):
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    for key, value in pedido.dict().items():
        setattr(db_pedido, key, value)

    db.commit()
    db.refresh(db_pedido)
    return db_pedido

def delete_pedido(db: Session, pedido_id: int):
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    # Liberar saldo congelado do comprador
    wallet_comprador = db.query(Wallet).filter(Wallet.usuario_id == db_pedido.CustomerID).first()
    if wallet_comprador:
        wallet_comprador.saldo_principal += db_pedido.preco_total
        wallet_comprador.saldo_congelado -= db_pedido.preco_total

    db.delete(db_pedido)
    db.commit()
    return db_pedido

def aceitar_pedido(db: Session, pedido_id: int, vendedor_id: int):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    produto = db.query(Produto).filter(Produto.id == pedido.produto_id, Produto.CustomerID == vendedor_id).first()
    if not produto:
        raise HTTPException(status_code=403, detail="Você não tem permissão para aceitar este pedido.")

    # Atualiza o estado para "Aceito pelo Vendedor"
    pedido.aceito_pelo_vendedor = True
    pedido.status = "Aceito pelo Vendedor"
    db.commit()

    return {"mensagem": "Pedido aceito com sucesso."}

def confirmar_recebimento_cliente(db: Session, pedido_id: int, cliente_id: int):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.CustomerID == cliente_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    # Atualiza o estado para "Recebido pelo Cliente"
    pedido.recebido_pelo_cliente = True
    pedido.status = "Recebido pelo Cliente"
    db.commit()

    return {"mensagem": "Recebimento confirmado pelo cliente."}

def liberar_saldo_vendedor(db: Session, pedido: Pedido):
    wallet_vendedor = db.query(Wallet).filter(Wallet.usuario_id == pedido.produto.CustomerID).first()
    if wallet_vendedor:
        wallet_vendedor.saldo_principal += pedido.preco_total
        wallet_vendedor.saldo_congelado -= pedido.preco_total
        db.commit()

def confirmar_pagamento_vendedor(db: Session, pedido_id: int, vendedor_id: int):
    pedido = db.query(Pedido).join(Produto).filter(Pedido.id == pedido_id, Produto.CustomerID == vendedor_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if not pedido.recebido_pelo_cliente:
        raise HTTPException(status_code=400, detail="O cliente ainda não confirmou o recebimento.")

    pedido.pagamento_confirmado = True
    pedido.status = "Pagamento Recebido"
    db.commit()

    # Se o pagamento e o recebimento forem confirmados, o pedido é finalizado
    if pedido.recebido_pelo_cliente and pedido.pagamento_confirmado:
        pedido.status = "Concluído"
        db.commit()

        # Atualiza o estoque do produto
        produto = db.query(Produto).filter(Produto.id == pedido.produto_id).first()
        if produto:
            produto.quantidade_estoque -= pedido.quantidade  # Atualiza a quantidade em estoque
            if produto.quantidade_estoque <= 0:
                produto.ativo = False  # Desativa o produto se o estoque acabar
            db.commit()

        # Libera o saldo do vendedor
        liberar_saldo_vendedor(db, pedido)

    return {"mensagem": "Pagamento confirmado e pedido concluído."}
