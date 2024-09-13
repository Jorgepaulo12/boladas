from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect,File,Form
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from typing import List, Dict
from models import *
from controlers.comentario import *
from controlers.denuncia_produto import *
from controlers.endereco_envio import *
from controlers.info_usuario import *
from controlers.item_pedido import *
from controlers.mensagem import *
from controlers.pedido import *
from controlers.produto import *
from controlers.usuario import *
from controlers.admin import *
from schemas import *
from auth import *
import json
import requests

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
url = "https://api.sandbox.vm.co.mz:18352/ipg/v1x/c2bPayment/singleStage/"
# Função para adicionar saldo usando M-Pesa (sem autenticação)
@app.post("/usuarios/{user_id}/adicionar_saldo/")
def adicionar_saldo_via_mpesa(user_id: int, msisdn: str, valor: int, db: Session = Depends(get_db)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Cabeçalhos e payload para a requisição M-Pesa
    # Cabeçalhos da solicitação
    token="XfsLebYAsnNPRsMu6JKfRPH9W5fhzSb+W3cdizVQ/Bm5ho2Xi/tn/Oo4bwHmFLqYlHQVnrog3MziMmxZLN5NnPEqCu5F9tLeYwmIo4mqNp544Ai5B8s+IAbxr//WLIS+pk992fp6uZl8IgFkQreqsN+leWSgQdeW7oiGl7Z5k6e10uc4xuD3KOEldtye0Pzjj0DmHNdhDh8SzpdgkjyEmWPhvyMwCVxn80pqaKAH5UUDGxv+dbY4HgsoAprMC+hclhHkVfk5VfqNlOToxpn6LmfeoZZ5BJJysEA/Y/T3zlK9JYq+dWahlWyMv+UoMEh7VG1lw3k/Hb7dqKkSRmrhStsuRrHjAITKRSoWv98ZWntQQua+Fz/BGV7v6f6qsytTBHCWVJD3qWl3phKztYWpr0CeJ3aGYns+gtKP04V2WdPrqVylYJFEQILGCfKmtFqYZ3rhdKhgs4UDAOQMCkED4uS+op0p+I6kW6ftAyw6WDu5dqQ5OFKV3++f/015kptDzRpoieB1EfUltgabnfWCNzivi7ZJY6S+5+ZJPDI9ORjYq+QlF+Qi/RQmJiGWDh+S/UY2sA2d9692lfmWKk3+10YAUoZlQTlq9qCvqVXYVwquiLkUpHhnpNMbidVBwuBM03IxA0SrmervTM7RY2mS1BXTwO2IQekX+9bnJ6+Tpkk="
    headers = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {token}",
           "Origin": "developer.mpesa.vm.co.mz"
    }

    # Dados da requisição
    data = {
        "input_TransactionReference": "T12344C",  # Gere uma referência única para cada transação
        "input_CustomerMSISDN": msisdn,           # Número de telefone do cliente
        "input_Amount": str(valor),               # Valor a ser carregado
        "input_ThirdPartyReference": "11114",     # Referência única de terceiros
        "input_ServiceProviderCode": "171717"     # Código do provedor de serviço
    }

   

# Enviar a requisição para a API da M-Pesa
    response = requests.post(url, headers=headers, data=json.dumps(data))

# Verifique se o status da resposta é de sucesso
    if response.status_code == 200 or response.status_code == 201:
    # Atualizar saldo do usuário na aplicação
     usuario.saldo += valor
     db.commit()
     db.refresh(usuario)
     return {"msg": "Saldo adicionado com sucesso!", "saldo_atual": usuario.saldo}
    else:
    # Exibir o conteúdo bruto da resposta para depuração
     print(f"Resposta da M-Pesa: {response.text}")
     raise HTTPException(status_code=400, detail=f"Erro ao processar a transação: {response.text}")


@app.get("/saldo/{user_id}")
def get_saldo(user_id: int, db: Session = Depends(get_db)):
    # Verifica se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Retorna o saldo diretamente
    return {"saldo": usuario.saldo}

# Rota para pegar os detalhes completos do produto
@app.get("/produto/detalhes/{produto_id}")
def produto_detalhado(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_detalhado(db, produto_id)



# Usuario routes
@app.post("/usuarios/")
def create_usuario_endpoint(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return create_usuario_db(db=db, usuario=usuario)

@app.get("/usuarios/{usuario_id}")
def read_usuario_endpoint(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = get_usuario(db=db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario

@app.put("/usuarios/{usuario_id}")
def update_usuario_endpoint(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    # Chame a função correta do controlador
    db_usuario = update_usuario_db(db=db, usuario_id=usuario_id, usuario=usuario)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario


@app.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = delete_usuario_db(db=db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario


@app.get("/produtos/")
def get_all_produtos(db: Session = Depends(get_db)):
    """
    Rota que retorna todos os produtos de todos os usuários.
    """
    produtos = db.query(Produto).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")
    return produtos


@app.get("/usuarios/{user_id}/produtos/")
def get_produtos_by_user(user_id: int, db: Session = Depends(get_db)):
    """
    Rota que retorna todos os produtos de um usuário específico.
    """
    produtos = db.query(Produto).filter(Produto.CustomerID == user_id).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado para este usuário.")
    return produtos




@app.get("/perfil/{usuario_id}")
def read_perfil(usuario_id: int, db: Session = Depends(get_db)):
    perfil = get_perfil(db=db, usuario_id=usuario_id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return perfil


# Admin routes
@app.post("/admins/",)
def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    return admin.create_admin(db=db, admin=admin)

@app.get("/admins/{admin_id}")
def read_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = get_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.put("/admins/{admin_id}")
def update_admin(admin_id: int, admin: AdminUpdate, db: Session = Depends(get_db)):
    db_admin = admin.update_admin(db=db, admin_id=admin_id, admin=admin)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.delete("/admins/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = delete_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.post("/info_usuarios/")
def create_info_usuario(info_usuario: InfoUsuarioCreate, db: Session = Depends(get_db)):
    return create_info_usuario_db(db=db, info_usuario=info_usuario)

@app.get("/info_usuarios/{info_usuario_id}")
def read_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = get_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

@app.put("/info_usuarios/{info_usuario_id}")
def update_info_usuario(info_usuario_id: int, info_usuario: InfoUsuarioUpdate, db: Session = Depends(get_db)):
    db_info_usuario = update_info_usuario_db(db=db, info_usuario_id=info_usuario_id, info_usuario=info_usuario)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

@app.delete("/info_usuarios/{info_usuario_id}")
def delete_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = delete_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

@app.post("/info_usuarios/{info_usuario_id}/perfil/")
async def upload_profile_picture(info_usuario_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    new_filename = save_image(file, PROFILE_UPLOAD_DIR)
    update_info_usuario_profile_picture(db, info_usuario_id, new_filename)
    return {"filename": new_filename}

@app.post("/info_usuarios/{info_usuario_id}/documento/")
async def upload_document_picture(info_usuario_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    new_filename = save_image(file, DOCUMENT_UPLOAD_DIR)
    update_info_usuario_document_picture(db, info_usuario_id, new_filename)
    return {"filename": new_filename}

# Comentario routes
@app.post("/comentarios/")
def create_comentario(comentario: ComentarioCreate, db: Session = Depends(get_db)):
    return create_comentario_db(db=db, comentario=comentario)

@app.get("/comentarios/{comentario_id}")
def read_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = get_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@app.put("/comentarios/{comentario_id}")
def update_comentario(comentario_id: int, comentario: ComentarioUpdate, db: Session = Depends(get_db)):
    db_comentario = update_comentario_db(db=db, comentario_id=comentario_id, comentario=comentario)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@app.delete("/comentarios/{comentario_id}")
def delete_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = delete_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

# DenunciaProduto routes
@app.post("/denuncia_produtos/")
def create_denuncia_produto(denuncia_produto: DenunciaProdutoCreate, db: Session = Depends(get_db)):
    return create_denuncia_produto_db(db=db, denuncia_produto=denuncia_produto)

@app.get("/denuncia_produtos/{denuncia_id}")
def read_denuncia_produto(denuncia_id: int, db: Session = Depends(get_db)):
    db_denuncia_produto = get_denuncia_produto(db=db, denuncia_id=denuncia_id)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto

@app.put("/denuncia_produtos/{denuncia_id}")
def update_denuncia_produto(denuncia_id: int, denuncia_produto: DenunciaProdutoUpdate, db: Session = Depends(get_db)):
    db_denuncia_produto = update_denuncia_produto_db(db=db, denuncia_id=denuncia_id, denuncia_produto=denuncia_produto)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto

@app.delete("/denuncia_produtos/{denuncia_id}")
def delete_denuncia_produto(denuncia_id: int, db: Session = Depends(get_db)):
    db_denuncia_produto = delete_denuncia_produto(db=db, denuncia_id=denuncia_id)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto


@app.post("/produto/{produto_id}/like")
def like_produto(produto_id: int, user_id: int, db: Session = Depends(get_db)):
    return toggle_like_produto(db, produto_id, user_id)

@app.get("/produto/{produto_id}/likes")
def produto_likes(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_likes(db, produto_id)



@app.post("/produtos/")
async def create_produto(
    nome: str = Form(...),
    preco: int = Form(...),
    quantidade_estoque: Optional[int] = Form(None),
    estado: str = Form(...),
    revisao: str = Form(...),
    disponiblidade: str = Form(...),
    descricao: str = Form(...),
    categoria: str = Form(...),
    detalhes: str = Form(...),
    tipo: str = Form(...),
    CustomerID: int = Form(...),
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # Verifica se pelo menos uma foto foi enviada
    if not fotos:
        raise HTTPException(status_code=400, detail="Pelo menos uma foto deve ser enviada.")
    
    # A primeira foto será a capa, as demais serão adicionais
    capa = fotos[0]
    outras_fotos = fotos[1:]

    # Criação do objeto ProdutoCreate para facilitar a passagem de dados
    produto_data = ProdutoCreate(
        nome=nome,
        preco=preco,
        quantidade_estoque=quantidade_estoque,
        estado=estado,
        revisao=revisao,
        disponiblidade=disponiblidade,
        descricao=descricao,
        categoria=categoria,
        detalhes=detalhes,
        tipo=tipo,
        CustomerID=CustomerID,
    )

    # Verifica se o usuário completou o registro antes de salvar o produto
    db_produto = create_produto_db_with_image(
        db=db, 
        produto=produto_data,
        user_id=CustomerID,
        files=fotos,  # Passa todas as fotos
        extra_files=outras_fotos  # Fotos adicionais
    )

    return {"message": "Produto criado com sucesso", "produto": db_produto}


# Rota para pegar os pedidos recebidos por um usuário específico
@app.get("/pedidos/recebidos/{user_id}")
def pedidos_recebidos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_recebidos(db, user_id)

# Rota para pegar os pedidos feitos por um usuário específico
@app.get("/pedidos/feitos/{user_id}")
def pedidos_feitos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_feitos(db, user_id)


@app.put("/produtos/{produto_id}")
async def update_produto(produto_id: int, produto: ProdutoUpdate, files: List[UploadFile] = File(None), db: Session = Depends(get_db)):
    db_produto = update_produto_db_with_images(db=db, produto_id=produto_id, produto=produto, files=files)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

@app.get("/produtos/{produto_id}")
def read_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = get_produto(db=db, produto_id=produto_id)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

@app.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = delete_produto(db=db, produto_id=produto_id)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto


@app.delete("/categorias/{categoria_id}")
def delete_categoria(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria =delete_categoria(db=db, categoria_id=categoria_id)
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return db_categoria

# Pedido routes
@app.post("/pedidos/")
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return create_pedido_db(db=db, pedido=pedido)

@app.get("/pedidos/{pedido_id}")
def read_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido = get_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@app.put("/pedidos/{pedido_id}")
def update_pedido(pedido_id: int, pedido: PedidoUpdate, db: Session = Depends(get_db)):
    db_pedido = update_pedido(db=db, pedido_id=pedido_id, pedido=pedido)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@app.delete("/pedidos/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido =delete_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

# Rota de criação de ItemPedido
@app.post("/item_pedidos/")
def create_item_pedido(item_pedido: ItemPedidoCreate, db: Session = Depends(get_db)):
    return create_item_pedido_db(db=db, item_pedido=item_pedido)    

@app.get("/item_pedidos/{item_pedido_id}")
def read_item_pedido(item_pedido_id: int, db: Session = Depends(get_db)):
    db_item_pedido = get_item_pedido(db=db, item_pedido_id=item_pedido_id)
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return db_item_pedido

@app.put("/item_pedidos/{item_pedido_id}")
def update_item_pedido(item_pedido_id: int, item_pedido: ItemPedidoUpdate, db: Session = Depends(get_db)):
    db_item_pedido = update_item_pedido_db(db=db, item_pedido_id=item_pedido_id, item_pedido=item_pedido)
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return db_item_pedido

@app.delete("/item_pedidos/{item_pedido_id}")
def delete_item_pedido(item_pedido_id: int, db: Session = Depends(get_db)):
    db_item_pedido = delete_item_pedido(db=db, item_pedido_id=item_pedido_id)
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return db_item_pedido

# EnderecoEnvio routes
@app.post("/enderecos_envio/")
def create_endereco_envio(endereco_envio: EnderecoEnvioCreate, db: Session = Depends(get_db)):
    return create_endereco_envio_db(db=db, endereco_envio=endereco_envio)

@app.get("/enderecos_envio/{endereco_envio_id}")
def read_endereco_envio(endereco_envio_id: int, db: Session = Depends(get_db)):
    db_endereco_envio = get_endereco_envio(db=db, endereco_envio_id=endereco_envio_id)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

@app.put("/enderecos_envio/{endereco_envio_id}")
def update_endereco_envio(endereco_envio_id: int, endereco_envio: EnderecoEnvioUpdate, db: Session = Depends(get_db)):
    db_endereco_envio = update_endereco_envio_db(db=db, endereco_envio_id=endereco_envio_id, endereco_envio=endereco_envio)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

@app.delete("/enderecos_envio/{endereco_envio_id}")
def delete_endereco_envio(endereco_envio_id: int, db: Session = Depends(get_db)):
    db_endereco_envio = delete_endereco_envio(db=db, endereco_envio_id=endereco_envio_id)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

# Mensagem routes

# Classe para gerenciar conexões WebSocket por usuário
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # Mapeia user_id para conexões WebSocket

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_private_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

manager = ConnectionManager()

# Rota de WebSocket para mensagens privadas em tempo real
@app.websocket("/ws/mensagens/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()  # Espera JSON com 'message' e 'to_user_id'
            message = data["message"]
            to_user_id = data["to_user_id"]

            # Envia a mensagem privada para o destinatário
            await manager.send_private_message(message, to_user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Rotas HTTP para gerenciar mensagens
@app.post("/mensagens/")
def create_mensagem_endpoint(mensagem: MensagemCreate, db: Session = Depends(get_db)):
    return create_mensagem_db(db=db, mensagem=mensagem)

@app.get("/mensagens/{mensagem_id}")
def read_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = get_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

@app.put("/mensagens/{mensagem_id}")
def update_mensagem_endpoint(mensagem_id: int, mensagem: MensagemUpdate, db: Session = Depends(get_db)):
    db_mensagem = update_mensagem_db(db=db, mensagem_id=mensagem_id, mensagem=mensagem)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

@app.delete("/mensagens/{mensagem_id}")
def delete_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = delete_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem





# Initialize the database
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
