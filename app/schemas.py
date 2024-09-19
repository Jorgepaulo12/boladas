from pydantic import BaseModel,EmailStr
from typing import Optional, List
from datetime import datetime
import enum

# Schemas para Usuário
class UsuarioBase(BaseModel):
    username: str
    email: EmailStr
    senha: Optional[str] = None  # Senha é opcional para login via Google
    google_id: Optional[str] = None  # Campo opcional para usuários do Google
    # Outros campos necessários
    tipo: Optional[str]=None


# Esquema para o token JWT
class Token(BaseModel):
    access_token: str
    token_type: str


class CategoriaBase(BaseModel):
    nome: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(CategoriaBase):
    pass





class UsuarioCreate(UsuarioBase):
    senha: str
    

class AdminBase(BaseModel):
    nome: str
    email: str

class AdminCreate(AdminBase):
    senha: str

class AdminUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str]
    senha: Optional[str] = None


class Admin(AdminBase):
    id: int

    class Config:
        orm_mode = True

# Schema base para InfoUsuario
class InfoUsuarioCreate(BaseModel):
    perfil: str
    provincia: str
    foto_bi: str
    distrito: str
    data_nascimento: str
    localizacao: str
    avenida: Optional[str] = None
    estado: str
    usuario_id:int
    bairro: Optional[str] = None






class ItemPedidoCreate(BaseModel):
    pedidoID: int
    produtoID: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True  # Atualize a configuração para o Pydantic v2

class ItemPedidoUpdate(ItemPedidoCreate):
    pedidoID: int
    produtoID: int
    quantidade: int
    preco_unitario: float



class InfoUsuarioUpdate(BaseModel):
    perfil: str
    provincia: str
    foto_bi: str
    distrito: str
    data_nascimento: str
    localizacao: str
    avenida: Optional[str] = None
    estado: str
    revisao: str
    bairro: Optional[str] = None



class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str]=None
    numero: Optional[str] = None
    whatsapp: Optional[str] = None
    tipo: Optional[str] = None
    estado: Optional[str] = None
    senha:Optional[str]=None
  

class ProdutoBase(BaseModel):
    nome: str
    preco: int
    quantidade_estoque: Optional[int] = None
    estado: str
    revisao: str
    disponiblidade: str
    descricao: str
    categoria: str
    detalhes:str
    tipo:str
    CustomerID: int

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    preco: Optional[int] = None
    quantidade_estoque: Optional[int] = None
    estado: Optional[str] = None
    revisao: Optional[str] = None
    disponiblidade: Optional[str] = None
    descricao: Optional[str] = None
    detalhes:Optional[str]=None
    tipo:Optional[str]=None
    categoria: Optional[int] = None
    CustomerID: Optional[int] = None
    data:datetime

# Schemas para Mensagem
class MensagemBase(BaseModel):
    remetenteID: int
    destinatarioID: int
    conteudo: str
    tipo_mensagem: str
    caminho_imagem: Optional[str] = None
    status: str

class MensagemCreate(MensagemBase):
    pass

class MensagemUpdate(BaseModel):
    conteudo: Optional[str] = None
    tipo_mensagem: Optional[str] = None
    caminho_imagem: Optional[str] = None
    status: Optional[str] = None

# Schemas para Pedido
class PedidoBase(BaseModel):
    CustomerID: int
    data_pedido: Optional[datetime] = None
    quantidade:int
    produto_id:int
    status: str

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    data_pedido: Optional[datetime] = None
    status: Optional[str] = None

# Schemas para Comentário
class ComentarioBase(BaseModel):
    produtoID: int
    CustomerID: int
    comentario: str
    data_comentario: datetime
    avaliacao: Optional[int] = None

class ComentarioCreate(ComentarioBase):
    pass

class ComentarioUpdate(BaseModel):
    comentario: Optional[str] = None
    avaliacao: Optional[int] = None

# Schemas para DenunciaProduto
class DenunciaProdutoBase(BaseModel):
    produtoID: int
    CustomerID: int
    motivo: str
    descricao: str
    data_denuncia: datetime
    status: str

class DenunciaProdutoCreate(DenunciaProdutoBase):
    pass

class DenunciaProdutoUpdate(BaseModel):
    motivo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[str] = None

# Schemas para Endereco_Envio
class EnderecoEnvioBase(BaseModel):
    endereco_line1: str
    endereco_line2: Optional[str] = None
    cidade: str
    CustomerID:int
    pedidoID:int
    estado: str
    codigo_postal: str
    pais: str

class EnderecoEnvioCreate(EnderecoEnvioBase):
    pass


class EmailSchema(BaseModel):
    email: str

class EnderecoEnvioUpdate(BaseModel):
    endereco_line1: Optional[str] = None
    endereco_line2: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    pais: Optional[str] = None
