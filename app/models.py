from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Table, DECIMAL,Float
from sqlalchemy.orm import relationship
from database import Base,engine
from datetime import datetime





produto_likes = Table(
    'produto_likes',
    Base.metadata,
    Column('produto_id', Integer, ForeignKey('produto.id'), primary_key=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True)
)

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    apelido = Column(String)
    username = Column(String, unique=True)
    email = Column(String, unique=True, nullable=True)
    numero = Column(String, unique=True, nullable=True)
    whatsapp = Column(String, nullable=True)
    senha = Column(String)
    tipo = Column(String)
    saldo = Column(Float, default=0.0)  # Novo campo de saldo
    
    # Relacionamento com a tabela InfoUsuario
    info_usuario = relationship("InfoUsuario", back_populates="usuario")
    produtos_curtidos = relationship(
        "Produto",
        secondary=produto_likes,
        back_populates="usuarios_que_deram_like"
    )

class InfoUsuario(Base):
    __tablename__ = "info_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    perfil = Column(String)
    provincia = Column(String)
    foto_bi = Column(String)
    distrito = Column(String)
    data_nascimento = Column(String)
    localizacao = Column(String)
    avenida = Column(String, nullable=True)
    estado = Column(String)
    revisao = Column(String)
    bairro = Column(String, nullable=True)
    
    # Relacionamento com Usuario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="info_usuario")

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True)
    senha = Column(String)


class Comentario(Base):
    __tablename__ = "comentario"
    comentarioID = Column(Integer, primary_key=True, index=True)
    produtoID = Column(Integer, ForeignKey("produto.id"))
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    comentario = Column(Text)
    data_comentario = Column(DateTime)
    avaliacao = Column(Integer, nullable=True)

class DenunciaProduto(Base):
    __tablename__ = "denunciaProduto"
    id = Column(Integer, primary_key=True, index=True)
    produtoID = Column(Integer, ForeignKey("produto.id"))
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    motivo = Column(String)
    descricao = Column(Text)
    data_denuncia = Column(DateTime)
    status = Column(String)

class Produto(Base):
    __tablename__ = "produto"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    capa = Column(String)
    fotos = Column(String)
    preco = Column(DECIMAL)
    quantidade_estoque = Column(Integer, nullable=True)
    estado = Column(String)
    revisao = Column(String)
    disponiblidade = Column(String)
    descricao = Column(Text)
    categoria = Column(String)
    detalhes=Column(String(1000))
    tipo=Column(String)
    data_publicacao = Column(DateTime, default=datetime.utcnow)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    likes = Column(Integer, default=0)
    data = Column(DateTime)
    usuarios_que_deram_like = relationship(
        "Usuario",
        secondary=produto_likes,
        back_populates="produtos_curtidos"
    )

    






class Pedido(Base):
    __tablename__ = "pedido"
    id = Column(Integer, primary_key=True, index=True)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    data_pedido = Column(DateTime)
    status = Column(String)

class ItemPedido(Base):
    __tablename__ = "item_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedidoID = Column(Integer, ForeignKey("pedido.id"))
    produtoID = Column(Integer, ForeignKey("produto.id"))
    quantidade = Column(Integer)
    preco_unitario = Column(DECIMAL)
    preco_total = Column(DECIMAL)

class EnderecoEnvio(Base):
    __tablename__ = "endereco_envio"
    id = Column(Integer, primary_key=True, index=True)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    pedidoID = Column(Integer, ForeignKey("pedido.id"))
    endereco_line1 = Column(String)
    endereco_line2 = Column(String, nullable=True)
    cidade = Column(String)
    estado = Column(String)
    codigo_postal = Column(String)
    pais = Column(String)

class Mensagem(Base):
    __tablename__ = "mensagem"
    id = Column(Integer, primary_key=True, index=True)
    remetenteID = Column(Integer, ForeignKey("usuarios.id"))
    destinatarioID = Column(Integer, ForeignKey("usuarios.id"))
    conteudo = Column(Text)
    data_mensagem = Column(DateTime)
    tipo_mensagem = Column(String)
    caminho_imagem = Column(String, nullable=True)
    status = Column(String)
