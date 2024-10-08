from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect,File,Form
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from typing import List, Dict
from fastapi.security import OAuth2PasswordRequestForm
from models import *
from passlib.context import CryptContext
from controlers.comentario import *
from controlers.denuncia_produto import *
from controlers.endereco_envio import *
from controlers.info_usuario import *
from controlers.mensagem import *
from controlers.pedido import *
from controlers.produto import *
from controlers.usuario import *
from controlers.pesquisa import *
from controlers.admin import *
from schemas import *
from auth import *
import json
import requests
import httpx
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,RedirectResponse
app = FastAPI()



#FUNCOES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#mpesa
url = "https://api.sandbox.vm.co.mz:18352/ipg/v1x/c2bPayment/singleStage/"
#google
GOOGLE_CLIENT_ID ="447649377867-1ff1uie6eeds2u3cq5er9virar9vden5.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/callback"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"Usuário {user_id} conectado")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"Usuário {user_id} desconectado")

    async def send_private_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)
            print(f"Mensagem enviada para o usuário {user_id}: {message}")
        else:
            print(f"Usuário {user_id} não está conectado")


#ROTAS DE POST

@app.post("/pedidos/{pedido_id}/aceitar/")
def aceitar_pedido_route(pedido_id: int, vendedor_id: int, db: Session = Depends(get_db)):
    return aceitar_pedido(db, pedido_id, vendedor_id)

@app.post("/pedidos/{pedido_id}/confirmar-recebimento/")
def confirmar_recebimento_route(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    return confirmar_recebimento_cliente(db, pedido_id, cliente_id)

@app.post("/pedidos/{pedido_id}/confirmar-pagamento/")
def confirmar_pagamento_route(pedido_id: int, vendedor_id: int, db: Session = Depends(get_db)):
    return confirmar_pagamento_vendedor(db, pedido_id, vendedor_id)

# Rota para promover um produto e criar um anúncio
@app.post("/produtos/{produto_id}/promover")
def promover_produto_route(
    produto_id: int, 
    dias: int, 
    titulo: str, 
    descricao: str, 
    tipo: str, 
    usuario_id: int, 
    db: Session = Depends(get_db)
):
    return promover_produto(produto_id, dias, db, usuario_id, titulo, descricao, tipo)


# Rota para o login (gera um token JWT com o ID do usuário se as credenciais estiverem corretas)
@app.post("/token")
def login_user(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # Autentica o usuário
    user = authenticate_user(db, form_data.username, form_data.password)

    # Verifica se a autenticação falhou
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera o token de acesso
    access_token = create_access_token(data={"sub": str(user.id)}, role="user")  # Inclui o ID do usuário no token
    
    # Retorna o token de acesso
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token/admin")
def login_admin(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    admin = authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(admin.id)}, role="admin")  # Usando o ID do admin no token
    return {"access_token": access_token, "token_type": "bearer"}


# Função para adicionar saldo usando M-Pesa (sem autenticação)
@app.post("/usuarios/{user_id}/adicionar_saldo/")
def adicionar_saldo_via_mpesa(msisdn: str, valor: int, db: Session = Depends(get_db),current_user: Usuario = Depends(get_current_user)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()

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
        "input_ThirdPartyReference": "11113",     # Referência única de terceiros
        "input_ServiceProviderCode": "171717"     # Código do provedor de serviço
    }

   
# Enviar a requisição para a API da M-Pesa
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code ==422:
        transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn, valor=valor, referencia=data["input_TransactionReference"], status="saldo insuficiente")
        db.add(transacao)
        db.commit()
        return {"msg": "Saldo insuficiente."}

    if response.status_code ==400:
        return {"msg": "ocorreu um erro"}
# Verifique se o status da resposta é de sucesso
    if response.status_code == 200 or response.status_code == 201:
    # Atualizar saldo do usuário na aplicação
     usuario.saldo += valor
     db.commit()
     db.refresh(usuario)
     # Registrar transação com sucesso
     transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn, valor=valor, referencia=data["input_TransactionReference"], status="sucesso")
     db.add(transacao)
     db.commit()
     return {"msg": "Saldo adicionado com sucesso!", "saldo_atual": usuario.saldo}
    else:
    # Exibir o conteúdo bruto da resposta para depuração
     print(f"Resposta da M-Pesa: {response.text}")
     raise HTTPException(status_code=400, detail=f"Erro ao processar a transação: {response.text}")

@app.post("/produtos/{produto_id}/reativar/")
def reativar_produto_endpoint(produto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return reativar_produto(produto_id=produto_id, current_user=current_user, db=db)    

@app.post("/recuperar_senha/")
def recuperar_senha(email_schema: EmailSchema, db: Session = Depends(get_db)):
    email = email_schema.email
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Verifica se o usuário tem uma senha configurada
    if not usuario.senha or usuario.senha == "":
        raise HTTPException(status_code=400, detail="Usuários cadastrados via Google não podem recuperar senha.")
    
    # Gera uma nova senha temporária
    nova_senha = gerar_senha_temporaria()

    hashed_senha = pwd_context.hash(nova_senha)
    usuario.senha = hashed_senha
    db.commit()

    # Envia a nova senha por e-mail
    subject = "Recuperação de Senha"
    body = f"Sua nova senha é: {nova_senha}"
    if not send_email(email, subject, body):
        raise HTTPException(status_code=500, detail="Falha ao enviar o e-mail de recuperação.")

    return {"msg": "Nova senha enviada para o e-mail informado."}

# Rotas HTTP para gerenciar mensagens
@app.post("/mensagenspost/")
async def create_message(mensagem: MensagemCreate, db: Session = Depends(get_db)):
    # Cria a mensagem no banco de dados
    db_mensagem = create_mensagem_db(db, mensagem)
    
    # Envia a mensagem para o WebSocket do destinatário
    to_user_id = mensagem.destinatarioID
    message_content = mensagem.conteudo
    # Envio da mensagem via WebSocket
    await manager.send_private_message(message_content, to_user_id)

    return db_mensagem

# EnderecoEnvio routes
@app.post("/enderecos_envio/")
def create_endereco_envio(endereco_envio: EnderecoEnvioCreate, db: Session = Depends(get_db)):
    return create_endereco_envio_db(db=db, endereco_envio=endereco_envio)


@app.post("/pedidos/")
def create_pedido(
    CustomerID: int = Form(...),
    produto_id: int = Form(...),
    quantidade: int = Form(...),
    status: str = Form(default="Pendente"),
    db: Session = Depends(get_db)
):
    # Cria o pedido usando a função existente no controlador
    pedido_data = PedidoCreate(
        CustomerID=CustomerID,
        produto_id=produto_id,
        quantidade=quantidade,
        status=status
    )
    
    # Salva o pedido e retorna o pedido criado
    pedido_criado = create_pedido_db(db=db, pedido=pedido_data)

    return {"mensagem": "Pedido criado com sucesso.", "pedido_id": pedido_criado.id}


# Admin routes
@app.post("/admins/")
def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    return register_admin(db=db, admin=admin)

@app.post("/usuarios/{usuario_id}/seguir")
def seguir_usuario_route(usuario_id: int, seguidor_id: int, db: Session = Depends(get_db)):
    # Chama a função que implementa a lógica de seguir um usuário
    resultado = seguir_usuario(db, usuario_id, seguidor_id)
    
    return resultado

@app.post("/usuarios/")
def create_usuario_endpoint(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Usando a função register_user para criar o usuário com hash de senha
    return register_user(db=db, user=usuario)

@app.post("/info_usuarios/")
async def create_info_usuario(
    fotos: List[UploadFile] = File(...),  # Lista de 3 fotos (frente, verso do BI, e foto do usuário com BI)
    provincia: str = Form(...),
    distrito: str = Form(...),
    data_nascimento: str = Form(...),
    localizacao: str = Form(...),
    estado: str = Form(...),  
    avenida: Optional[str] = Form(None),
    nacionalidade:Optional[str]=Form(None),
    bairro: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validação para garantir que 3 fotos sejam enviadas
    if len(fotos) != 3:
        raise HTTPException(status_code=400, detail="Você deve enviar exatamente 3 fotos: frente, verso do BI, e uma foto sua com o BI.")

    # Salvando as imagens
    perfil_filename = save_image(fotos[2], PROFILE_UPLOAD_DIR)  # Foto do usuário segurando o BI (3ª foto)
    bi_frente_filename = save_image(fotos[0], DOCUMENT_UPLOAD_DIR)  # Foto da frente do BI (1ª foto)
    bi_tras_filename = save_image(fotos[1], DOCUMENT_UPLOAD_DIR)  # Foto do verso do BI (2ª foto)

    # Criando o objeto InfoUsuarioCreate para facilitar a passagem de dados
    info_usuario_data = InfoUsuarioCreate(
        perfil=perfil_filename,
        provincia=provincia,
        foto_bi=f"{bi_frente_filename},{bi_tras_filename},{perfil_filename}",  # Fotos concatenadas
        distrito=distrito,
        data_nascimento=data_nascimento,
        localizacao=localizacao,
        estado=estado,
        usuario_id=current_user.id,
        avenida=avenida,
        nacionalidade=nacionalidade,
        bairro=bairro
    )

    # Criando a entrada no banco de dados
    #db_info_usuario = create_info_usuario_db(db=db, info_usuario=info_usuario_data, current_user_id=current_user.id)
    db_info_usuario = create_info_usuario_db(db=db, info_usuario=info_usuario_data, current_user=current_user.id)

    return {"message": "Informações do usuário criadas com sucesso", "info_usuario": db_info_usuario}

# Comentario routes
@app.post("/comentarios/")
def create_comentario(comentario: ComentarioCreate, db: Session = Depends(get_db)):
    return create_comentario_db(db=db, comentario=comentario)


@app.post("/info_usuarios/{info_usuario_id}/perfil/")
async def upload_profile_picture(
    perfil: Usuario = Depends(get_current_user),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Verifique o tipo de arquivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser uma imagem")

    # Salva a imagem no servidor
    new_filename = save_image(file, PROFILE_UPLOAD_DIR)

    # Atualiza a foto de perfil no banco de dados
    update_info_usuario_profile_picture(db, perfil, new_filename)

    return {"filename": new_filename}


@app.post("/produtos/")
async def create_produto(
    nome: str = Form(...),
    preco: int = Form(...),
    quantidade_estoque: Optional[int] = Form(None),
    estado: str = Form(...),
    distrito:str=Form(...),
    provincia:str=Form(...),
    localizacao:str=Form(...),
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
        provincia=provincia,
        distrito=distrito,
        localizacao=localizacao,
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

# DenunciaProduto routes
@app.post("/denuncia_produtos/")
def create_denuncia_produto(denuncia_produto: DenunciaProdutoCreate, db: Session = Depends(get_db)):
    return create_denuncia_produto_db(db=db, denuncia_produto=denuncia_produto)

@app.post("/produto/{produto_id}/like")
def like_produto(produto_id: int, user_id: int, db: Session = Depends(get_db)):
    return toggle_like_produto(db, produto_id, user_id)

#ROTAS DE GET

# Rota para obter todas as transações de um usuário específico
@app.get("/usuarios/{user_id}/transacoes/")
def listar_transacoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Verificar se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id ==  current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Buscar todas as transações do usuário
    transacoes = db.query(Transacao).filter(Transacao.usuario_id == current_user.id).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes

@app.get("/transacoes/")
def listar_todas_transacoes(db: Session = Depends(get_db)):
    # Buscar todas as transações do sistema
    transacoes = db.query(Transacao).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes

# Rota para obter todas as transações de um usuário específico
@app.get("/usuarios/{user_id}/transacoes/")
def listar_transacoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Verificar se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id ==  current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Buscar todas as transações do usuário
    transacoes = db.query(Transacao).filter(Transacao.usuario_id == current_user.id).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes

@app.get("/imagens/{nome_imagem}")
def obter_imagem(nome_imagem: str, current_user: Usuario = Depends(get_current_user)):
    imagem = os.path.join("uploads/produto", nome_imagem)

    if not os.path.exists(imagem):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")

    # Retorna a imagem como resposta (após verificar permissões)
    return FileResponse(imagem)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos os domínios. Ajuste conforme necessário.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos HTTP.
    allow_headers=["*"],  # Permitir todos os cabeçalhos.
)


@app.get("/anuncios/")
def listar_anuncios(db: Session = Depends(get_db)):
    """
    Rota para listar todos os anúncios válidos junto com os produtos associados.
    """
    return listar_anuncios_com_produtos(db)

@app.get("/produtos/promovidos/")
def listar_produtos_promovidos(db: Session = Depends(get_db)):
    return get_produtos_promovidos(db)

@app.get("/auth/callback")
async def google_auth_callback(code: str, db: Session = Depends(get_db)):
    # Troca o código de autorização por um token de acesso
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URI, data=data)
        token_json = token_response.json()

        if "access_token" not in token_json:
            raise HTTPException(status_code=400, detail="Erro ao obter token de acesso")

        access_token = token_json["access_token"]

        # Obter as informações do usuário autenticado
        userinfo_response = await client.get(GOOGLE_USERINFO_URI, headers={"Authorization": f"Bearer {access_token}"})
        userinfo = userinfo_response.json()

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        nome_completo = userinfo.get("name")
        primeiro_nome = userinfo.get("given_name")
        sobrenome = userinfo.get("family_name")
        foto_perfil = userinfo.get("picture")  # Foto do perfil

        # Verifica se o usuário já existe no banco de dados pelo google_id ou email
        user = db.query(Usuario).filter((Usuario.google_id == google_id) | (Usuario.email == email)).first()

        if not user:
            # Se o usuário não existir, cria um novo
            new_user = Usuario(
                email=email,
                nome=primeiro_nome,
                google_id=google_id,
                username=sobrenome,  # Sobrenome como username
                senha=None,  # Não salvamos senha para usuários do Google
                foto_perfil=foto_perfil  # Armazena a foto do perfil
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        # Cria o token JWT para o usuário existente ou recém-criado
        access_token = create_access_token(data={"sub": str(user.id)})

        # Redireciona para a página de produtos
        redirect_url = f"http://localhost:5000/auth/callback"
        return RedirectResponse(url=redirect_url)

@app.get("/produtos/pesquisa/")
def pesquisa_avancada(termo: str, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """
    Rota para pesquisa avançada de produtos com base em um termo de busca que pode
    corresponder a nome, preço, descrição, categoria, detalhes, tipo, província, estado ou distrito.
    A consulta é paginada com o número de produtos limitado por página.
    
    - `termo`: Termo de busca
    - `page`: Número da página (padrão: 1)
    - `limit`: Limite de produtos por página (padrão: 10)
    """
    produtos = executar_pesquisa_avancada(termo=termo, page=page, limit=limit, db=db)
    return produtos

@app.get("/enderecos_envio/{endereco_envio_id}")
def read_endereco_envio(endereco_envio_id: int, db: Session = Depends(get_db)):
    db_endereco_envio = get_endereco_envio(db=db, endereco_envio_id=endereco_envio_id)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

@app.get("/mensagens/{mensagem_id}")
def read_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = get_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

@app.get("/produtos/{produto_id}")
def read_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = get_produto(db=db, produto_id=produto_id)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

# Rota para pegar os pedidos feitos por um usuário específico
@app.get("/pedidos/feitos/{user_id}")
def pedidos_feitos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_feitos(db, user_id)

@app.get("/pedidos/{pedido_id}")
def read_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido = get_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@app.get("/categorias/peso/")
def calcular_peso_categorias_route(db: Session = Depends(get_db), top_n: int = 5):
    """
    Rota para calcular o peso (frequência de pesquisa) das categorias mais pesquisadas.
    
    Args:
        db (Session): Sessão do banco de dados.
        top_n (int): Número de categorias mais pesquisadas a serem consideradas (padrão: 5).
    
    Returns:
        Lista de categorias e seus pesos (número de pesquisas).
    """
    return calcular_peso_categorias_mais_pesquisadas(db=db, top_n=top_n)

@app.get("/usuarios/nao_verificados/")
def obter_usuarios_nao_verificados(db: Session = Depends(get_db)):
    """
    Rota para obter todos os usuários não verificados.
    
    Returns:
        List[Usuario]: Lista de usuários não verificados.
    """
    usuarios_nao_verificados = listar_usuarios_nao_verificados(db=db)
    return usuarios_nao_verificados

@app.get("/conversas/{usuario1_id}/{usuario2_id}")
def get_conversas(usuario1_id: int, usuario2_id: int, db: Session = Depends(get_db)):
    conversas = get_conversas_entre_usuarios(db, usuario1_id, usuario2_id)
    return conversas

@app.get("/pesquisas/lista")
def listar_pesquisas_route(page: int = 1, limit: int = 10, usuario_id: int = None, db: Session = Depends(get_db)):
    """
    Rota para listar todas as pesquisas realizadas, com opção de filtrar por usuário.
    
    Args:
        page (int): Página de resultados.
        limit (int): Limite de resultados por página.
        usuario_id (int, opcional): ID do usuário para filtrar as pesquisas.
    
    Returns:
        Lista de pesquisas.
    """
    return listar_pesquisas(db=db, usuario_id=usuario_id, page=page, limit=limit)

@app.get("/saldo")
def get_saldo(db: Session = Depends(get_db), 
              current_user: Usuario = Depends(get_current_user)):  # Usuário autenticado é extraído automaticamente
    
    # Verifica se o usuário existe no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Retorna o saldo do usuário autenticado
    return {"saldo": usuario.saldo}

# Rota para pegar os detalhes completos do produto
@app.get("/produto/detalhes/{produto_id}")
def produto_detalhado(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_detalhado(db, produto_id)


@app.get("/usuarios/{usuario_id}")
def read_usuario_endpoint(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = get_usuario(db=db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario

@app.get("/produtos/{produto_id}")
def visualizar_produto(produto_id: int, db: Session = Depends(get_db)):
    """
    Rota que retorna os detalhes de um produto e incrementa o número de visualizações.
    
    Args:
        produto_id (int): ID do produto a ser visualizado.
        db (Session): Sessão do banco de dados.
    
    Returns:
        Produto: Retorna os detalhes do produto.
    """
    # Usar a função get_produto para buscar e incrementar visualizações
    produto = get_produto(db=db, produto_id=produto_id)

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    return produto  # Retorna o produto encontrado e atualizado


@app.get("/produtos/")
def listar_produtos(db: Session = Depends(get_db)):
    """
    Rota que lista todos os produtos com prioridade para:
    - Produtos recentes (últimos 30 minutos).
    - Depois, aplicar pesos baseados em promoções, likes e visualizações.
    """
    produtos = db.query(Produto).all()

    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")
    
    # Passar tanto 'produtos' quanto 'db' para a função 'combinar_produtos'
    produtos_ordenados = combinar_produtos(produtos, db)
    
    return produtos_ordenados

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

@app.get("/usuarios/{usuario_id}/notificacoes/")
def listar_notificacoes(usuario_id: int, db: Session = Depends(get_db)):
    notificacoes = db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id).all()
    return notificacoes

@app.get("/usuarios/{usuario_id}/seguindo")
def get_usuario_seguindo(usuario_id: int, db: Session = Depends(get_db)):
    return get_seguidores(usuario_id, db)

@app.get("/admins/{admin_id}")
def read_admins(admin_id: int, db: Session = Depends(get_db)):
    db_admin = get_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.get("/produto/{produto_id}/likes")
def produto_likes(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_likes(db, produto_id)

# Rota para pegar os pedidos recebidos por um usuário específico
@app.get("/pedidos/recebidos/{user_id}")
def pedidos_recebidos(user_id: int, db: Session = Depends(get_db)):
    return get_pedidos_recebidos(db, user_id)

@app.get("/comentarios/{comentario_id}")
def read_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = get_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@app.get("/denuncia_produtos/{denuncia_id}")
def read_denuncia_produto(denuncia_id: int, db: Session = Depends(get_db)):
    db_denuncia_produto = get_denuncia_produto(db=db, denuncia_id=denuncia_id)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto

@app.get("/info_usuarios/{info_usuario_id}")
def read_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = get_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

#ROTAS DE DELITE
@app.delete("/pesquisas/{pesquisa_id}/")
def eliminar_pesquisa_route(pesquisa_id: int, db: Session = Depends(get_db)):
    """
    Rota para eliminar uma pesquisa específica pelo seu ID.
    
    Args:
        pesquisa_id (int): ID da pesquisa a ser eliminada.
    
    Returns:
        Mensagem de sucesso.
    """
    return eliminar_pesquisa(db=db, pesquisa_id=pesquisa_id)

@app.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    db_usuario = delete_usuario_db(db=db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"msg": "Usuário excluído com sucesso"}

@app.delete("/mensagens/{mensagem_id}")
def delete_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = delete_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

@app.delete("/pedidos/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido =delete_pedido(db=db, pedido_id=pedido_id)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@app.delete("/item_pedidos/{item_pedido_id}")
def delete_item_pedido(item_pedido_id: int, db: Session = Depends(get_db)):
    db_item_pedido = delete_item_pedido(db=db, item_pedido_id=item_pedido_id)
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return db_item_pedido

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

@app.delete("/denuncia_produtos/{denuncia_id}")
def delete_denuncia_produto(denuncia_id: int, db: Session = Depends(get_db)):
    db_denuncia_produto = delete_denuncia_produto(db=db, denuncia_id=denuncia_id)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto

@app.delete("/enderecos_envio/{endereco_envio_id}")
def delete_endereco_envio(endereco_envio_id: int, db: Session = Depends(get_db)):
    db_endereco_envio = delete_endereco_envio(db=db, endereco_envio_id=endereco_envio_id)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

@app.delete("/comentarios/{comentario_id}")
def delete_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = delete_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@app.delete("/admins/{admin_id}")
def delete_admins(admin_id: int, db: Session = Depends(get_db)):
    db_admin = delete_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.delete("/info_usuarios/{info_usuario_id}")
def delete_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = delete_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario
#ROTAS DE PUT

@app.put("/admins/{admin_id}")
def update_admins(admin_id: int, admin: AdminUpdate, db: Session = Depends(get_db)):
    db_admin = update_admin(db=db, admin_id=admin_id, admin=admin)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

@app.put("/usuarios/{usuario_id}")
def update_usuario_endpoint(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    # Chame a função correta do controlador
    db_usuario = update_usuario_db(db=db, usuario_id=usuario_id, usuario=usuario)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario

@app.put("/usuarios/{user_id}/atualizar_senha/")
def atualizar_senha(user_id: int, senha_atual: str, nova_senha: str, db: Session = Depends(get_db)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Verificar se o usuário foi cadastrado via Google (ou outro OAuth)
    if not usuario.senha or usuario.senha == "":
        raise HTTPException(status_code=400, detail="Usuários cadastrados via Google não podem alterar a senha.")

    # Verificar se a senha atual está correta
    if not verify_password(senha_atual, usuario.senha):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    # Criptografar a nova senha
    hashed_nova_senha = hash_password(nova_senha)

    # Atualizar a senha no banco de dados
    usuario.senha = hashed_nova_senha
    db.commit()

    return {"msg": "Senha atualizada com sucesso."}

@app.put("/info_usuarios/{info_usuario_id}")
def update_info_usuario(info_usuario: InfoUsuarioUpdate, db: Session = Depends(get_db),info_usuario_id:Usuario = Depends(get_current_user),):
    db_info_usuario = update_info_usuario_db(db=db, info_usuario_id=info_usuario_id, info_usuario=info_usuario)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

@app.put("/info_usuarios/{info_usuario_id}/revisao/")
def update_revisao(
    info_usuario_id: int,
    nova_revisao: str = Form(...),  # O valor da nova revisão será enviado pela requisição
    motivo: str = Form(None),  # O motivo será enviado se a revisão for negativa
    db: Session = Depends(get_db),  # A sessão do banco de dados é obtida via Dependência
    #current_admin: AdminModel = Depends(get_current_admin) Protege a rota apenas para administradores
):
    # Buscar o usuário no banco de dados
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.id == info_usuario_id).first()

    if not db_info_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Se a revisão for negativa, o motivo é obrigatório
    if nova_revisao == "não" and not motivo:
        raise HTTPException(status_code=400, detail="Motivo é obrigatório quando a revisão é negativa.")

    # Atualizar a revisão do usuário
    db_info_usuario.revisao = nova_revisao
    if motivo:
        db_info_usuario.motivo_revisao = motivo

    db.commit()
    db.refresh(db_info_usuario)

    return {"message": "Revisão atualizada com sucesso", "info_usuario": db_info_usuario}

@app.put("/comentarios/{comentario_id}")
def update_comentario(comentario_id: int, comentario: ComentarioUpdate, db: Session = Depends(get_db)):
    db_comentario = update_comentario_db(db=db, comentario_id=comentario_id, comentario=comentario)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@app.put("/denuncia_produtos/{denuncia_id}")
def update_denuncia_produto(denuncia_id: int, denuncia_produto: DenunciaProdutoUpdate, db: Session = Depends(get_db)):
    db_denuncia_produto = update_denuncia_produto_db(db=db, denuncia_id=denuncia_id, denuncia_produto=denuncia_produto)
    if db_denuncia_produto is None:
        raise HTTPException(status_code=404, detail="DenunciaProduto not found")
    return db_denuncia_produto

@app.put("/produtos/{produto_id}")
async def update_produto(produto_id: int, produto: ProdutoUpdate, files: List[UploadFile] = File(None), db: Session = Depends(get_db)):
    db_produto = update_produto_db_with_images(db=db, produto_id=produto_id, produto=produto, files=files)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

@app.put("/pedidos/{pedido_id}")
def update_pedido(pedido_id: int, pedido: PedidoUpdate, db: Session = Depends(get_db)):
    db_pedido = update_pedido(db=db, pedido_id=pedido_id, pedido=pedido)
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return db_pedido

@app.put("/enderecos_envio/{endereco_envio_id}")
def update_endereco_envio(endereco_envio_id: int, endereco_envio: EnderecoEnvioUpdate, db: Session = Depends(get_db)):
    db_endereco_envio = update_endereco_envio_db(db=db, endereco_envio_id=endereco_envio_id, endereco_envio=endereco_envio)
    if db_endereco_envio is None:
        raise HTTPException(status_code=404, detail="EnderecoEnvio not found")
    return db_endereco_envio

# Mensagem routes

manager = ConnectionManager()

@app.websocket("/ws/mensagens/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int,db: Session = Depends(get_db)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            message = data["message"]
            to_user_id = data["to_user_id"]

            # Armazena a mensagem no banco de dados
            mensagem = MensagemCreate(
                remetenteID=user_id,
                destinatarioID=to_user_id,
                conteudo=message,
                data_mensagem=datetime.utcnow(),
                tipo_mensagem='texto',
                status='enviado'
            )
            create_mensagem_db(db, mensagem)

            # Envia a mensagem privada para o destinatário
            await manager.send_private_message(message, to_user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.put("/mensagens/{mensagem_id}")
def update_mensagem_endpoint(mensagem_id: int, mensagem: MensagemUpdate, db: Session = Depends(get_db)):
    db_mensagem = update_mensagem_db(db=db, mensagem_id=mensagem_id, mensagem=mensagem)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

# Rota para desativar o usuário
@app.put("/usuario/{usuario_id}/desativar")
def desativar_usuario_route(usuario_id: int, db: Session = Depends(get_db)):
    return desativar_usuario(db, usuario_id)

# Rota para ativar o usuário
@app.put("/usuario/{usuario_id}/ativar")
def ativar_usuario_route(usuario_id: int, db: Session = Depends(get_db)):
    return ativar_usuario(db, usuario_id)

# Initialize the database
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.62", port=8000) 
