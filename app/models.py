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
    username = Column(String(255), unique=True, index=True)
    nome=Column(String(50))
    email = Column(String(255), unique=True, index=True)
    senha = Column(String(255), nullable=True)  # Pode ser null para login com Google
    google_id = Column(String(255), unique=True, nullable=True) 
    tipo = Column(String(255),nullable=True)
    saldo = Column(Float, default=0.0)  # Novo campo de saldo
    foto_perfil = Column(String(50), nullable=True)
    ativo = Column(Boolean, default=True) 
    notificacoes = relationship("Notificacao", back_populates="usuario")
    pesquisas = relationship("Pesquisa", back_populates="usuario") 
    transacoes = relationship("Transacao", back_populates="usuario")
    
    # Relacionamento com a tabela InfoUsuario
    info_usuario = relationship("InfoUsuario", back_populates="usuario")
    produtos_curtidos = relationship(
        "Produto",
        secondary=produto_likes,
        back_populates="usuarios_que_deram_like"
    )

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255))
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(String(200))




class InfoUsuario(Base):
    __tablename__ = "info_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    perfil = Column(String(350))
    provincia = Column(String(350))
    foto_bi = Column(String(350))
    distrito = Column(String(350))
    data_nascimento = Column(String(350))
    localizacao = Column(String(350))
    avenida = Column(String(255), nullable=True)
    estado = Column(String(350))
    nacionalidade=Column(String(255),nullable=True)
    revisao = Column(String(255), default="não")
    bairro = Column(String(255), nullable=True)
    
    # Relacionamento com Usuario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="info_usuario")



class Pesquisa(Base):
    __tablename__ = "pesquisas"

    id = Column(Integer, primary_key=True, index=True)
    termo_pesquisa = Column(String, index=True)
    categoria_pesquisa = Column(String, nullable=True)  # Categoria do termo de pesquisa
    data_pesquisa = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # ID do usuário (opcional)

    usuario = relationship("Usuario", back_populates="pesquisas")


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
    motivo = Column(String(350))
    descricao = Column(Text)
    data_denuncia = Column(DateTime)
    status = Column(String(350))


class Produto(Base):
    __tablename__ = "produto"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(350))
    capa = Column(String(350))
    fotos = Column(String(350))
    preco = Column(DECIMAL)
    quantidade_estoque = Column(Integer, nullable=True)
    estado = Column(String(350))
    provincia=Column(String(20))
    distrito=Column(String(20))
    localizacao=(String(100))
    revisao = Column(String(350))
    disponiblidade = Column(String(350))
    descricao = Column(Text)
    categoria = Column(String(350))
    detalhes = Column(String(1000))
    tipo = Column(String(350))
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
    titulo = Column(String(350))
    descricao = Column(Text)
    tipo_anuncio = Column(String(350))  # Exemplo: "promocional", "normal", etc.
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



class Transacao(Base):
    __tablename__ = "transacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    msisdn = Column(String, nullable=False)  # Número do cliente
    valor = Column(Integer, nullable=False)   # Valor da transação
    referencia = Column(String, nullable=False)  # Referência da transação M-Pesa
    status = Column(String, nullable=False)  # Status da transação (sucesso, erro, etc.)
    data_hora = Column(DateTime, default=datetime.utcnow)  # Data e hora da transação

    usuario = relationship("Usuario", back_populates="transacoes")

class Notificacao(Base):
    __tablename__ = "notificacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    mensagem = Column(String(255), nullable=False)
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
    status = Column(String(350))  # Estado do pedido, como "Pendente", "Aceito", "Enviado", etc.
    
    # Novos campos para o controle de aceitação e confirmação
    aceito_pelo_vendedor = Column(Boolean, default=False)  # O vendedor aceitou o pedido?
    recebido_pelo_cliente = Column(Boolean, default=False)  # O cliente confirmou o recebimento?
    pagamento_confirmado = Column(Boolean, default=False)  # O vendedor confirmou o pagamento?


class EnderecoEnvio(Base):
    __tablename__ = "endereco_envio"
    id = Column(Integer, primary_key=True, index=True)
    CustomerID = Column(Integer, ForeignKey("usuarios.id"))
    pedidoID = Column(Integer, ForeignKey("pedido.id"))
    endereco_line1 = Column(String(350))
    endereco_line2 = Column(String(255), nullable=True)
    cidade = Column(String(350))
    estado = Column(String(350))
    codigo_postal = Column(String(350))
    pais = Column(String(350))

class Mensagem(Base):
    __tablename__ = "mensagem"
    id = Column(Integer, primary_key=True, index=True)
    remetenteID = Column(Integer, ForeignKey("usuarios.id"))
    destinatarioID = Column(Integer, ForeignKey("usuarios.id"))
    conteudo = Column(Text)
    data_mensagem = Column(DateTime)
    tipo_mensagem = Column(String(350))
    caminho_imagem = Column(String(255), nullable=True)
    status = Column(String(350))