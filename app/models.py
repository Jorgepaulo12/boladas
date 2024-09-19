from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Table, DECIMAL,Float, Boolean
from sqlalchemy.orm import relationship
from database import Base,engine
from datetime import datetime,timedelta





produto_likes = Table(
    'produto_likes',
    Base.metadata,
    Column('produto_id', Integer, ForeignKey('produto.id'), primary_key=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True)
)

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    nome=Column(String(50))
    email = Column(String, unique=True, index=True)
    senha = Column(String, nullable=True)  # Pode ser null para login com Google
    google_id = Column(String, unique=True, nullable=True) 
    tipo = Column(String,nullable=True)
    saldo = Column(Float, default=0.0)  # Novo campo de saldo
    notificacoes = relationship("Notificacao", back_populates="usuario") 
    
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
    revisao = Column(String, default="não")
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
    detalhes = Column(String(1000))
    tipo = Column(String)
    visualizacoes = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    likes = Column(Integer, default=0)
    data_publicacao = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com Anuncio (um para um)
    anuncio = relationship('Anuncio', back_populates='produto')

    def verificar_status(self):
        if datetime.utcnow() > self.data_publicacao + timedelta(days=30):
            self.ativo = False

    usuarios_que_deram_like = relationship(
        "Usuario",
        secondary=produto_likes,
        back_populates="produtos_curtidos"
    )

class Anuncio(Base):
    __tablename__ = "anuncio"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descricao = Column(Text)
    tipo_anuncio = Column(String)  # Exemplo: "promocional", "normal", etc.
    produto_id = Column(Integer, ForeignKey("produto.id"), unique=True)
    promovido_em = Column(DateTime, default=datetime.utcnow)
    expira_em = Column(DateTime, nullable=True)
    
    produto = relationship('Produto', back_populates='anuncio')

    def definir_promocao(self, dias: int):
        self.expira_em = datetime.utcnow() + timedelta(days=dias)
class Seguidor(Base):
    __tablename__ = "seguidores"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    seguidor_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamento entre usuários
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    seguidor = relationship("Usuario", foreign_keys=[seguidor_id])


class Notificacao(Base):
    __tablename__ = "notificacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    mensagem = Column(String, nullable=False)
    data = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="notificacoes")



class Pedido(Base):
    __tablename__ = "pedido"
    id = Column(Integer, primary_key=True, index=True)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    produto_id = Column(Integer, ForeignKey("produto.id"))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(DECIMAL)
    preco_total = Column(DECIMAL)
    data_pedido = Column(DateTime, default=datetime.utcnow)
    status = Column(String)



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
