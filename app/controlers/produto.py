import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from models import Produto, Usuario, InfoUsuario,Comentario,produto_likes,Seguidor,Notificacao,Anuncio,Wallet
from schemas import ProdutoCreate, ProdutoUpdate
from datetime import datetime, timedelta
from sqlalchemy import func
from controlers.pedido import enviar_notificacao
from sqlalchemy.future import select
import random
from unidecode import unidecode

from slugify import slugify

PRODUCT_UPLOAD_DIR = "uploads/produto"
os.makedirs(PRODUCT_UPLOAD_DIR, exist_ok=True)

def save_image(file: UploadFile, upload_dir: str) -> str:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado não é uma imagem válida.")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return unique_filename

def save_images(files: List[UploadFile], upload_dir: str) -> List[str]:
    return [save_image(file, upload_dir) for file in files]

LIMITE_DIARIO = 3
VALOR_PARA_PUBLICAR = 25.0





def create_produto_db_with_image( 
    db: Session, 
    produto: ProdutoCreate, 
    files: List[UploadFile],  
    user_id: int,
    extra_files: List[UploadFile]
):
    # Verifica se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Verifica se o usuário passou pela revisão
    info_usuario = db.query(InfoUsuario).filter(InfoUsuario.usuario_id == user_id).first()
    if not info_usuario:
        raise HTTPException(status_code=404, detail="Informações do usuário não encontradas.")
    
    if info_usuario.revisao != "sim":
        raise HTTPException(status_code=403, detail="Usuário não passou pela revisão e não pode publicar produtos.")
    
    # Verifica se as imagens foram enviadas
    if not files:
        raise HTTPException(status_code=400, detail="Nenhuma imagem foi enviada.")
    
    # Verifica se a conta PRO do usuário expirou
    usuario.verificar_expiracao_pro()
    
    # Verifica quantos produtos o usuário já publicou hoje
    hoje = datetime.utcnow().date()  # Considera a data UTC
    produtos_hoje = db.query(Produto).filter(
        Produto.CustomerID == user_id,
        Produto.data_publicacao >= hoje
    ).count()
    
    LIMITE_DIARIO = 5  # Limite diário de publicações para contas PRO
    VALOR_PARA_PUBLICAR = 10.0  # Valor necessário para publicar se o limite diário for atingido

    # Obter a carteira do usuário
    wallet = db.query(Wallet).filter(Wallet.usuario_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Carteira do usuário não encontrada.")
    
    # Se o usuário é PRO e não atingiu o limite diário, permite a publicação sem custo
    if usuario.conta_pro:
        if produtos_hoje >= LIMITE_DIARIO:
            raise HTTPException(status_code=403, detail="Você atingiu o limite diário de publicações para sua conta PRO.")
    else:
        # Se o usuário não é PRO, verifica se ele tem saldo suficiente para publicar
        if produtos_hoje >= LIMITE_DIARIO:
            # Se o saldo principal for suficiente, deduz o valor do saldo
            if wallet.saldo_principal >= VALOR_PARA_PUBLICAR:
                wallet.saldo_principal -= VALOR_PARA_PUBLICAR
            elif wallet.saldo_principal + wallet.bonus >= VALOR_PARA_PUBLICAR:
                # Se não houver saldo principal, mas houver bônus, deduz do bônus
                wallet.bonus -= VALOR_PARA_PUBLICAR - wallet.saldo_principal
                wallet.saldo_principal = 0  # Define saldo principal para 0
            else:
                raise HTTPException(status_code=403, detail="Saldo insuficiente para publicar o produto.")
    
    # Salva a primeira imagem como capa
    capa_filename = save_image(files[0], PRODUCT_UPLOAD_DIR)
    
    # Salva as fotos adicionais
    image_filenames = save_images(extra_files, PRODUCT_UPLOAD_DIR)
    
    # Cria o produto no banco de dados
    db_produto = Produto(
        **produto.dict(), 
        capa=capa_filename, 
        fotos=",".join(image_filenames),  # Armazena as fotos adicionais
        data_publicacao=datetime.utcnow()  # Adiciona a data de publicação
    )
    
    db.add(db_produto)
    db.commit()  # Commit para salvar o produto
    
    # Commit para atualizar o saldo do usuário
    db.commit()
    
    # Envia notificação de que o usuário publicou um produto
    mensagem_notificacao = f"{usuario.nome} publicou um novo produto!"
    enviar_notificacoes_para_seguidores(db, usuario.id, mensagem_notificacao)

    return db_produto



def get_produtos_promovidos(db: Session):
    """
    Retorna todos os produtos que estão atualmente promovidos (anunciados).
    """
    # Busca os produtos que possuem anúncios válidos (não expirados)
    produtos_promovidos = db.query(Produto).join(Anuncio).filter(
        Anuncio.data_expiracao > datetime.utcnow()
    ).all()

    if not produtos_promovidos:
        raise HTTPException(status_code=404, detail="Nenhum produto promovido encontrado.")

    return produtos_promovidos




def seguir_usuario(db: Session, usuario_id: int, seguidor_id: int):
    # Verificar se o seguidor e o usuário existem
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    seguidor = db.query(Usuario).filter(Usuario.id == seguidor_id).first()

    if not usuario or not seguidor:
        raise HTTPException(status_code=404, detail="Usuário ou seguidor não encontrado.")
    
    
    if usuario_id == seguidor_id:
         raise HTTPException(status_code=400, detail="voce nao pode se seguir")
    # Verificar se já está seguindo
    ja_seguindo = db.query(Seguidor).filter(Seguidor.usuario_id == usuario_id, Seguidor.seguidor_id == seguidor_id).first()

    if ja_seguindo:
        raise HTTPException(status_code=400, detail="Já está seguindo esse usuário.")
    
    # Criar novo registro de seguidor
    novo_seguidor = Seguidor(usuario_id=usuario_id, seguidor_id=seguidor_id)
    db.add(novo_seguidor)
    db.commit()

    # Enviar notificação para o usuário que está sendo seguido
    mensagem = f"{seguidor.nome} começou a seguir você!"  # Mensagem personalizada
    enviar_notificacao(db, usuario_id, mensagem)

    return {"mensagem": f"Agora você está seguindo {usuario.nome}!"}

  


# Função para obter seguidores de um usuário
def get_seguidores(usuario_id: int, db: Session):
    # Verifica se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Obter a lista de pessoas que o usuário segue
    seguindo = db.query(Seguidor).filter(Seguidor.usuario_id == usuario_id).all()

    # Obter o total de pessoas que ele segue
    total_seguindo = db.query(func.count(Seguidor.id)).filter(Seguidor.usuario_id == usuario_id).scalar()

    # Formatar a lista de seguidores com detalhes dos usuários
    seguindo_list = [
        {
            "id": seguidor.seguidor.id,
            "nome": seguidor.seguidor.nome,
            "username": seguidor.seguidor.username,
            "email": seguidor.seguidor.email
        } 
        for seguidor in seguindo
    ]

    return {
        "total_seguindo": total_seguindo,
        "seguindo": seguindo_list
    }

def toggle_like_produto(db: Session, produto_id: int, user_id: int):
    # Verifica se o produto existe
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Verifica se o usuário já deu like neste produto
    like_existente = db.query(produto_likes).filter_by(produto_id=produto_id, usuario_id=user_id).first()

    if like_existente:
        # Se o like já existir, remove o like
        produto.likes -= 1
        db.execute(produto_likes.delete().where(produto_likes.c.produto_id == produto_id).where(produto_likes.c.usuario_id == user_id))
        message = "Like removido com sucesso!"
    else:
        # Se o like não existir, adiciona um like
        produto.likes += 1
        db.execute(produto_likes.insert().values(produto_id=produto_id, usuario_id=user_id))
        message = "Like adicionado com sucesso!"
    
    # Comita a transação
    db.commit()

    return {"message": message, "total_likes": produto.likes}






def reativar_produto(produto_id: int, current_user: Usuario, db: Session):
    # Buscar o produto no banco de dados
    produto = db.query(Produto).filter(Produto.id == produto_id).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    if produto.ativo:
        raise HTTPException(status_code=400, detail="Produto já está ativo.")

    # Verificar saldo do usuário
    if current_user.saldo < 25:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para reativar o produto.")

    # Descontar saldo e reativar o produto
    current_user.saldo -= 25
    produto.ativo = True
    produto.data_publicacao = datetime.utcnow()  # Atualizar a data de publicação para reiniciar o ciclo de 30 dias
    db.commit()

    return {"msg": "Produto reativado com sucesso!"}



def atualizar_status_produtos(db: Session):
    produtos = db.query(Produto).all()
    for produto in produtos:
        if produto.ativo and datetime.utcnow() > produto.data_publicacao + timedelta(days=30):
            produto.ativo = False
            db.commit()




def gerar_slug(nome_produto: str) -> str:
    nome_sem_acento = unidecode(nome_produto)  # Remove acentos e caracteres especiais
    return slugify(nome_sem_acento)  # Gera o slug amigável

def gerar_slug_unico(nome_produto: str, db: Session) -> str:
    slug_base = gerar_slug(nome_produto)
    slug = slug_base
    contador = 1

    # Verifica se já existe um produto com o mesmo slug
    while db.query(Produto).filter(Produto.slug == slug).first() is not None:
        slug = f"{slug_base}-{contador}"
        contador += 1

    return slug
def get_produto_likes(db: Session, produto_id: int):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Conta o número de likes do produto
    likes_count = db.query(produto_likes).filter_by(produto_id=produto_id).count()
    
    return {"produto_id": produto_id, "likes": likes_count}




def listar_anuncios_com_produtos(db: Session):
    stmt = (
        select(Anuncio, Produto)
        .join(Produto, Anuncio.produto_id == Produto.id)
    )
    result = db.execute(stmt)
    anuncios = [
        {
            "anuncio": {
                "id": anuncio.id,
                "titulo": anuncio.titulo,
                "descricao": anuncio.descricao,
                "tipo_anuncio": anuncio.tipo_anuncio,
                "produto_id": anuncio.produto_id,
                "expira_em": anuncio.expira_em.isoformat() if anuncio.expira_em else None,
                "promovido_em": anuncio.promovido_em.isoformat() if anuncio.promovido_em else None
            },
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "descricao": produto.descricao,
                "preco": produto.preco,
                "capa":produto.capa,
                "likes":produto.likes,
                "views":produto.visualizacoes
            }
        }
        for anuncio, produto in result
    ]
    return anuncios



def get_produto_detalhado(db: Session, slug: str):
    """
    Retorna os detalhes do produto, incluindo foto, nome, comentários, categoria, preço,
    nome do usuário que publicou, data, disponibilidade, total de likes e usuários que deram like,
    e incrementa o número de visualizações do produto.
    
    Args:
        db (Session): Sessão do banco de dados.
        slug (str): Slug do produto.
    
    Returns:
        dict: Detalhes do produto.
    """
    # Busca o produto pelo slug
    produto = db.query(Produto).filter(Produto.slug == slug).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Incrementa o número de visualizações
    produto.visualizacoes += 1
    db.add(produto)
    db.commit()
    db.refresh(produto)
    
    # Busca o usuário que publicou o produto
    usuario = db.query(Usuario).filter(Usuario.id == produto.CustomerID).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário que publicou o produto não encontrado.")
    
    # Busca os comentários do produto
    comentarios = db.query(Comentario).filter(Comentario.produtoID == produto.id).all()
    
    # Busca os likes (usuários que curtiram o produto)
    usuarios_que_deram_like = db.query(Usuario).join(produto_likes).filter(produto_likes.c.produto_id == produto.id).all()
    total_likes = len(usuarios_que_deram_like)  # Total de likes
    
    # Retorna os detalhes em um dicionário
    return {
        "nome": produto.nome,
        "detalhe": produto.detalhes,
        "tipo": produto.tipo,
        "foto_capa": produto.capa,
        "preco": produto.preco,
        "slug": produto.slug,
        "disponibilidade": produto.disponiblidade,
        "data_publicacao": produto.data_publicacao,  # Supondo que exista esse campo
        "visualizacoes": produto.visualizacoes,  # Inclui o campo de visualizações
        "usuario": {
            "nome": usuario.nome,
            "email": usuario.email
        },
        "categoria": produto.categoria,
        "comentarios": [
            {
                "comentario": comentario.comentario,
                "avaliacao": comentario.avaliacao,
                "data_comentario": comentario.data_comentario
            } for comentario in comentarios
        ],
        "likes": {
            "total": total_likes,
            "usuarios": [
                {
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "email": usuario.email
                }
                for usuario in usuarios_que_deram_like
            ]
        }
    }




def enviar_notificacoes_para_seguidores(db: Session, usuario_id: int, mensagem: str):
    # Buscar seguidores
    seguidores = db.query(Seguidor).filter(Seguidor.usuario_id == usuario_id).all()

    # Enviar notificação para cada seguidor
    for seguidor in seguidores:
        nova_notificacao = Notificacao(
            usuario_id=seguidor.seguidor_id,
            mensagem=mensagem
        )
        db.add(nova_notificacao)
    db.commit()





def update_produto_db_with_images(db: Session, produto_id: int, produto: ProdutoUpdate, files: Optional[List[UploadFile]] = None):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Atualiza os dados do produto
    for key, value in produto.dict().items():
        setattr(db_produto, key, value)
    
    # Se houver novas imagens, salva e atualiza
    if files:
        new_image_filenames = save_images(files, PRODUCT_UPLOAD_DIR)
        db_produto.fotos = ",".join(new_image_filenames)
    
    db.commit()
    db.refresh(db_produto)
    
    return db_produto



def selecionar_produtos_por_peso(produtos: List[Produto], db: Session):
    """
    Seleciona produtos ponderados por promoção, likes e visualizações.
    
    Args:
        produtos (List[Produto]): Lista de produtos.
        db (Session): Sessão do banco de dados para consultar anúncios.

    Returns:
        List[Produto]: Lista de produtos selecionados de maneira ponderada.
    """
    total_score = 0
    weights = []

    for produto in produtos:
        # Peso básico baseado em visualizações e likes
        score = produto.visualizacoes + (2 * produto.likes)
        
        # Verificar se o produto está promovido consultando a tabela de anúncios
        anuncio = db.query(Anuncio).filter(Anuncio.produto_id == produto.id).first()
        if anuncio:
            score *= 1.5  # Aumentar o peso dos produtos promovidos
        
        total_score += score
        weights.append(score)

    # Evitar divisão por zero
    if total_score == 0:
        return produtos

    # Normalizar os pesos para criar probabilidades relativas
    normalized_weights = [weight / total_score for weight in weights]

    # Selecionar os produtos com base nos pesos normalizados
    selected_produtos = random.choices(produtos, weights=normalized_weights, k=len(produtos))

    return selected_produtos


def filtrar_produtos_recentes(produtos: List[Produto]):
    """
    Filtra produtos publicados nos últimos 30 minutos.

    Args:
        produtos (List[Produto]): Lista de produtos.
    
    Returns:
        List[Produto]: Lista de produtos recentes.
    """
    trinta_minutos_atras = datetime.utcnow() - timedelta(minutes=30)
    
    # Filtrando produtos onde a data_publicacao não é None e o produto foi publicado nos últimos 30 minutos
    produtos_recentes = [
        produto for produto in produtos 
        if produto.data_publicacao is not None and produto.data_publicacao > trinta_minutos_atras
    ]
    
    return produtos_recentes


def combinar_produtos(produtos: List[Produto], db: Session):
    """
    Combina produtos recentes e ponderados por peso (promoção, visualizações, likes).
    
    Args:
        produtos (List[Produto]): Lista completa de produtos.
        db (Session): Sessão do banco de dados para consultar anúncios.

    Returns:
        List[Produto]: Lista de produtos ordenados com prioridade para produtos recentes.
    """
    # Filtrar produtos recentes (últimos 30 minutos)
    produtos_recentes = filtrar_produtos_recentes(produtos)
    
    # Filtrar produtos não recentes (mais de 30 minutos)
    produtos_nao_recentes = [produto for produto in produtos if produto not in produtos_recentes]
    
    # Ordenar produtos recentes por data de criação (mais recentes primeiro)
    produtos_recentes.sort(key=lambda produto: produto.data_publicacao, reverse=True)
    
    # Aplicar a seleção ponderada aos produtos não recentes
    produtos_ponderados = selecionar_produtos_por_peso(produtos_nao_recentes, db)
    
    # Combinar os resultados: Recentes primeiro, seguidos pelos ponderados
    return produtos_recentes + produtos_ponderados



def get_all_produtos(db: Session):
    """
    Função para buscar todos os produtos ativos e com revisão marcada como 'sim'.
    
    Args:
        db (Session): Sessão do banco de dados.
    
    Returns:
        List[Produto]: Lista de produtos ativos e com revisão 'sim'.
    """
    produtos = db.query(Produto).filter(Produto.ativo == True, Produto.revisao == "sim").all()

    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto ativo encontrado com revisão 'sim'.")
    
    return produtos


def get_produtos_by_user(db: Session, user_id: int):
    """
    Função para buscar todos os produtos de um usuário específico.
    
    Args:
        db (Session): Sessão do banco de dados.
        user_id (int): ID do usuário para o qual queremos buscar os produtos.
    
    Returns:
        List[Produto]: Lista de produtos encontrados para o usuário.
    """
    produtos = db.query(Produto).filter(Produto.CustomerID == user_id).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado para este usuário.")
    return produtos






# Função para promover um produto e criar um anúncio
def promover_produto(produto_id: int, dias: int, db: Session, usuario_id: int, titulo: str, descricao: str, tipo: str):
    # Busca o produto
    produto = db.query(Produto).filter(Produto.id == produto_id).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Verificar se o usuário tem saldo suficiente
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    custo_promocao = dias * 0
    if usuario.saldo < custo_promocao:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para promover o produto")

    # Descontar o saldo do usuário
    usuario.saldo -= custo_promocao
    db.commit()

    # Criar o anúncio vinculado ao produto
    anuncio = Anuncio(
        produto_id=produto.id,
        #usuario_id=usuario.id,
        titulo=titulo,
        descricao=descricao,
        tipo_anuncio=tipo,
        promovido_em=datetime.utcnow(),
        expira_em=datetime.utcnow() + timedelta(days=dias)
    )
    db.add(anuncio)
    db.commit()

    return {"message": f"Produto promovido por {dias} dias e colocado em anúncio", "produto": produto, "anuncio": anuncio}

def get_produto(db: Session, slug: str):
    """
    Recupera um produto pelo slug e incrementa o número de visualizações.

    Args:
        db (Session): Sessão do banco de dados.
        slug (str): Slug do produto.

    Returns:
        Produto: Instância do produto se encontrado, caso contrário None.
    """
    # Buscar o produto no banco de dados pelo slug
    produto = db.query(Produto).filter(Produto.slug == slug).first()

    if not produto:
        return None  # Retorna None se o produto não for encontrado

    # Incrementar o número de visualizações
    produto.visualizacoes += 1

    # Salvar as alterações no banco de dados
    db.add(produto)
    db.commit()
    db.refresh(produto)

    return produto


    return produto  # Retorna o produto atualizado

