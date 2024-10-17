from controlers.produto import *
from controlers.pesquisa import *
from schemas import *
from auth import *
from fastapi import APIRouter,Form,File

router=APIRouter(prefix="/produtos",tags=["rotas de produtos"])


# Rota para promover um produto e criar um anúncio
@router.post("/{produto_id}/promover")
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


@router.post("/{produto_id}/reativar/")
def reativar_produto_endpoint(produto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return reativar_produto(produto_id=produto_id, current_user=current_user, db=db) 


@router.post("/publicar")
async def create_produto(
    nome: str = Form(...),
    preco: int = Form(...),
    quantidade_estoque: Optional[int] = Form(None),
    estado: str = Form(...),
    distrito: str = Form(...),
    provincia: str = Form(...),
    localizacao: str = Form(...),
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

    # Criação do objeto ProdutoCreate
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

    # Gera o slug único
    slug = gerar_slug_unico(produto_data.nome, db)
    produto_data.slug = slug  # Atribui o slug gerado ao produto
    # Verifica se o usuário completou o registro antes de salvar o produto
    db_produto = create_produto_db_with_image(
        db=db, 
        produto=produto_data,
        user_id=CustomerID,
        files=fotos,  # Passa todas as fotos
        extra_files=outras_fotos  # Fotos adicionais
    )

    return {"message": "Produto criado com sucesso", "produto": db_produto}


@router.get("/pesquisa/")
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

@router.get("/{slug}")
def read_produto(slug: str, db: Session = Depends(get_db)):
    # Busca o produto pelo slug no banco de dados
    db_produto = db.query(Produto).filter(Produto.slug == slug).first()
    
    # Verifica se o produto foi encontrado
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return db_produto

@router.get("/detalhes/{slug}")
def produto_detalhado(slug: str, db: Session = Depends(get_db)):
    return get_produto_detalhado(db, slug)

@router.get("/produto/{produto_id}/likes")
def produto_likes(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_likes(db, produto_id)

@router.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = delete_produto(db=db, produto_id=produto_id)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

# A rota precisa de `Form` para receber JSON junto com arquivos
@router.put("/produtos/{produto_id}")
async def update_produto(
    produto_id: int,
    nome: Optional[str] = Form(None),
    preco: Optional[float] = Form(None),
    quantidade_estoque: Optional[int] = Form(None),
    estado: Optional[str] = Form(None),
    disponiblidade: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    detalhes: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
    categoria: Optional[int] = Form(None),
    CustomerID: Optional[int] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Transforme os dados recebidos via Form em um dicionário para atualizar o produto
    produto = ProdutoUpdate(
        nome=nome,
        preco=preco,
        quantidade_estoque=quantidade_estoque,
        estado=estado,
        disponiblidade=disponiblidade,
        descricao=descricao,
        detalhes=detalhes,
        tipo=tipo,
        categoria=categoria,
        CustomerID=CustomerID,
      
    )
    
    # Função de atualização do produto
    db_produto = update_produto_db_with_images(db=db, produto_id=produto_id, produto=produto, files=files)
    
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return db_produto


@router.post("/produto/{produto_id}/like")
def like_produto(produto_id: int, user_id: int, db: Session = Depends(get_db)):
    return toggle_like_produto(db, produto_id, user_id)


@router.get("/anuncios/")
def listar_anuncios(db: Session = Depends(get_db)):
    """
    Rota para listar todos os anúncios válidos junto com os produtos associados.
    """
    return listar_anuncios_com_produtos(db)

@router.get("/promovidos/")
def listar_produtos_promovidos(db: Session = Depends(get_db)):
    return get_produtos_promovidos(db)


@router.get("/produtos/")
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


@router.get("/usuarios/{user_id}/produtos/")
def get_produtos_by_user(user_id: int, db: Session = Depends(get_db)):
    """
    Rota que retorna todos os produtos de um usuário específico.
    """
    produtos = db.query(Produto).filter(Produto.CustomerID == user_id).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado para este usuário.")
    return produtos