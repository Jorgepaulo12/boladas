from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from models import Produto,Pesquisa
from sqlalchemy import func
from fastapi import HTTPException

def salvar_pesquisa(termo: str, categoria: str, db: Session, usuario_id: int = None):
    """
    Função para salvar a pesquisa do usuário no banco de dados.
    
    Args:
        termo (str): O termo pesquisado.
        categoria (str): A categoria relacionada ao termo.
        db (Session): Sessão do banco de dados.
        usuario_id (int, opcional): O ID do usuário, se estiver logado.
    """
    pesquisa = Pesquisa(
        termo_pesquisa=termo,
        categoria_pesquisa=categoria,
        data_pesquisa=datetime.utcnow(),
        usuario_id=usuario_id  # Se o usuário não estiver logado, o ID será None
    )
    db.add(pesquisa)
    db.commit()
    db.refresh(pesquisa)









def executar_pesquisa_avancada(termo: str, page: int, limit: int, db: Session,usuario_id: int = None):
    """
    Pesquisa avançada por produtos com base em um termo, que pode corresponder a preço, descrição, 
    categoria, detalhes, tipo, província ou distrito.
    Aplica paginação conforme page e limit.
    """
    # Divide o termo de busca em palavras-chave separadas por espaço
    termos = termo.split()

    # Cria a consulta base
    query = db.query(Produto)
    
    # Aplica os filtros dinamicamente para cada palavra-chave
    for palavra in termos:
        # Busca em várias colunas
        query = query.filter(
            or_(
                Produto.nome.ilike(f"%{palavra}%"),
                Produto.preco.ilike(f"%{palavra}%"),          # Pesquisa por preço (convertido em string)
                Produto.descricao.ilike(f"%{palavra}%"),      # Pesquisa por descrição
                Produto.categoria.ilike(f"%{palavra}%"),      # Pesquisa por categoria
                Produto.detalhes.ilike(f"%{palavra}%"),       # Pesquisa por detalhes
                Produto.tipo.ilike(f"%{palavra}%"),           # Pesquisa por tipo
                Produto.provincia.ilike(f"%{palavra}%"),      # Pesquisa por província
                Produto.estado.ilike(f"%{palavra}%"),         # Pesquisa por estado
                Produto.distrito.ilike(f"%{palavra}%")        # Pesquisa por distrito
            )
        )

    # Adiciona paginação
    produtos = query.offset((page - 1) * limit).limit(limit).all()
    if produtos:
        categoria = produtos[0].categoria
    # Se nenhum produto for encontrado, retorna todos os produtos
    if not produtos:
        produtos = db.query(Produto).offset((page - 1) * limit).limit(limit).all()
        salvar_pesquisa(termo=termo, categoria=categoria, db=db, usuario_id=usuario_id) 
    if produtos == []:     
        salvar_pesquisa(termo=termo, categoria=categoria, db=db, usuario_id=usuario_id)
        
    return produtos



def executar_pesquisa_avancada(termo: str, page: int, limit: int, db: Session, usuario_id: int = None):
    """
    Pesquisa avançada por produtos com base em um termo, que pode corresponder a preço, descrição, 
    categoria, detalhes, tipo, província ou distrito.
    Aplica paginação conforme `page` e `limit`. Lista apenas produtos ativos e com revisão "sim".
    """
    # Divide o termo de busca em palavras-chave separadas por espaço
    termos = termo.split()

    # Cria a consulta base e aplica os filtros de produto ativo e com revisão "sim"
    query = db.query(Produto).filter(Produto.ativo == True, Produto.revisao == "sim")
    
    # Aplica os filtros dinamicamente para cada palavra-chave
    for palavra in termos:
        # Busca em várias colunas
        query = query.filter(
            or_(
                Produto.nome.ilike(f"%{palavra}%"),
                Produto.preco.ilike(f"%{palavra}%"),          # Pesquisa por preço (convertido em string)
                Produto.descricao.ilike(f"%{palavra}%"),      # Pesquisa por descrição
                Produto.categoria.ilike(f"%{palavra}%"),      # Pesquisa por categoria
                Produto.detalhes.ilike(f"%{palavra}%"),       # Pesquisa por detalhes
                Produto.tipo.ilike(f"%{palavra}%"),           # Pesquisa por tipo
                Produto.provincia.ilike(f"%{palavra}%"),      # Pesquisa por província
                Produto.estado.ilike(f"%{palavra}%"),         # Pesquisa por estado
                Produto.distrito.ilike(f"%{palavra}%")        # Pesquisa por distrito
            )
        )
    # Adiciona paginação
    produtos = query.offset((page - 1) * limit).limit(limit).all()
    if produtos:
        categoria = produtos[0].categoria
    # Se nenhum produto for encontrado, retorna todos os produtos
    if not produtos:
        produtos = db.query(Produto).offset((page - 1) * limit).limit(limit).all()
        salvar_pesquisa(termo=termo, categoria=categoria, db=db, usuario_id=usuario_id) 
    if produtos == []:     
        salvar_pesquisa(termo=termo, db=db, usuario_id=usuario_id)
        
    return produtos

def eliminar_pesquisa(db: Session, pesquisa_id: int = None, usuario_id: int = None):
    """
    Elimina uma pesquisa específica ou todas as pesquisas de um usuário.
    
    Args:
        db (Session): Sessão do banco de dados.
        pesquisa_id (int, opcional): ID da pesquisa a ser eliminada.
        usuario_id (int, opcional): ID do usuário cujas pesquisas devem ser eliminadas.
    
    Raises:
        HTTPException: Se a pesquisa ou usuário não forem encontrados.
    
    Returns:
        Mensagem de sucesso.
    """
    if pesquisa_id:
        # Deletar uma pesquisa específica
        pesquisa = db.query(Pesquisa).filter(Pesquisa.id == pesquisa_id).first()
        if not pesquisa:
            raise HTTPException(status_code=404, detail="Pesquisa não encontrada.")
        db.delete(pesquisa)
    elif usuario_id:
        # Deletar todas as pesquisas de um usuário
        pesquisas = db.query(Pesquisa).filter(Pesquisa.usuario_id == usuario_id).all()
        if not pesquisas:
            raise HTTPException(status_code=404, detail="Nenhuma pesquisa encontrada para esse usuário.")
        for pesquisa in pesquisas:
            db.delete(pesquisa)
    else:
        raise HTTPException(status_code=400, detail="ID da pesquisa ou do usuário deve ser fornecido.")
    
    db.commit()
    return {"msg": "Pesquisa(s) eliminada(s) com sucesso."}




def listar_pesquisas(db: Session, usuario_id: int = None, page: int = 1, limit: int = 10):
    """
    Lista todas as pesquisas realizadas, com a possibilidade de filtrar por usuário específico.
    
    Args:
        db (Session): Sessão do banco de dados.
        usuario_id (int, opcional): ID do usuário para filtrar as pesquisas (ou None para listar todas).
        page (int): Página de resultados (padrão: 1).
        limit (int): Limite de resultados por página (padrão: 10).
    
    Returns:
        Lista de pesquisas.
    """
    query = db.query(Pesquisa)
    
    # Se um usuário for especificado, filtra as pesquisas desse usuário
    if usuario_id:
        query = query.filter(Pesquisa.usuario_id == usuario_id)
    
    # Paginação
    pesquisas = query.offset((page - 1) * limit).limit(limit).all()
    
    return pesquisas


def calcular_peso_categorias_mais_pesquisadas(db: Session, top_n: int = 5):
    """
    Calcula o peso (frequência de pesquisa) das categorias mais pesquisadas.
    
    Args:
        db (Session): Sessão do banco de dados.
        top_n (int): Número de categorias mais pesquisadas a serem consideradas (padrão: 5).
    
    Returns:
        Lista de dicionários com categorias e seus pesos (quantidade de pesquisas).
    """
    # Seleciona as categorias mais pesquisadas e conta o número de vezes que foram pesquisadas
    categorias_mais_pesquisadas = db.query(
        Pesquisa.categoria_pesquisa,
        func.count(Pesquisa.categoria_pesquisa).label('total_pesquisas')
    ).group_by(Pesquisa.categoria_pesquisa).order_by(func.count(Pesquisa.categoria_pesquisa).desc()).limit(top_n).all()

    resultados = []
    
    # Cria a lista de resultados com categoria e peso (total de pesquisas)
    for categoria, total_pesquisas in categorias_mais_pesquisadas:
        resultados.append({
            "categoria": categoria,
            "peso": total_pesquisas  # Peso é o número de pesquisas realizadas para essa categoria
        })
    
    return resultados
