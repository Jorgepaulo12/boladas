import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from models import Produto, Usuario, InfoUsuario,Comentario,produto_likes
from schemas import ProdutoCreate, ProdutoUpdate
from datetime import datetime, timedelta

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
    
    # Verifica quantos produtos o usuário já publicou hoje
    hoje = datetime.utcnow().date()  # Considera a data UTC
    produtos_hoje = db.query(Produto).filter(
        Produto.CustomerID == user_id,
        Produto.data_publicacao >= hoje
    ).count()
    
    # Verifica se o limite diário foi atingido
    if produtos_hoje >= LIMITE_DIARIO:
        # Se o limite foi atingido, verifica o saldo do usuário
        if usuario.saldo < VALOR_PARA_PUBLICAR:
            raise HTTPException(status_code=403, detail="Saldo insuficiente para publicar o produto.")
        
        # Deduz o valor do saldo do usuário
        usuario.saldo -= VALOR_PARA_PUBLICAR
    
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
    
    # Atualiza o saldo do usuário
    db.commit()  # Commit para atualizar o saldo do usuário
    
    return db_produto

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




def get_produto_likes(db: Session, produto_id: int):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Conta o número de likes do produto
    likes_count = db.query(produto_likes).filter_by(produto_id=produto_id).count()
    
    return {"produto_id": produto_id, "likes": likes_count}



def get_produto_detalhado(db: Session, produto_id: int):
    """
    Retorna os detalhes do produto, incluindo foto, nome, comentários, categoria, preço,
    nome do usuário que publicou, data, disponibilidade, total de likes e usuários que deram like.
    
    Args:
        db (Session): Sessão do banco de dados.
        produto_id (int): ID do produto.
    
    Returns:
        dict: Detalhes do produto.
    """
    # Busca o produto pelo ID
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Busca o usuário que publicou o produto
    usuario = db.query(Usuario).filter(Usuario.id == produto.CustomerID).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário que publicou o produto não encontrado.")
    
    # Busca os comentários do produto
    comentarios = db.query(Comentario).filter(Comentario.produtoID == produto_id).all()
    
    # Busca os likes (usuários que curtiram o produto)
    usuarios_que_deram_like = db.query(Usuario).join(produto_likes).filter(produto_likes.c.produto_id == produto_id).all()
    total_likes = len(usuarios_que_deram_like)  # Total de likes
    
    # Retorna os detalhes em um dicionário
    return {
        "nome": produto.nome,
        "detalhe": produto.detalhes,
        "tipo": produto.tipo,
        "foto_capa": produto.capa,
        "preco": produto.preco,
        "disponibilidade": produto.disponiblidade,
        "data_publicacao": produto.data,  # Supondo que exista esse campo
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



def get_all_produtos(db: Session):
    """
    Função para buscar todos os produtos no banco de dados.
    
    Args:
        db (Session): Sessão do banco de dados.
    
    Returns:
        List[Produto]: Lista de todos os produtos encontrados.
    """
    produtos = db.query(Produto).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")
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


def get_produto(db: Session, produto_id: int):
    """
    Recupera um produto pelo ID.

    Args:
        db (Session): Sessão do banco de dados.
        produto_id (int): ID do produto.

    Returns:
        Produto: Instância do produto se encontrado, caso contrário None.
    """
    return db.query(Produto).filter(Produto.id == produto_id).first()
