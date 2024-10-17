from sqlalchemy.orm import Session
from database import SessionLocal, engine
from typing import List, Dict

from models import Base
from fastapi import FastAPI
from routers.admin import router as admin_router
from routers.comentario import router as comentario_router
from routers.denuncia_produto import router as denuncia_produto_router
from routers.endereco_envio import router as endereco_envio_router
from routers.info_usuario import router as info_usuario_router
from routers.mensagem import router as mensagem_router
from routers.pedido import router as pedido_router
from routers.produto import router as produto_router
from routers.usuario import router as usuario_router
from routers.pesquisa import router as pesquisa_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos os domínios. Ajuste conforme necessário.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos HTTP.
    allow_headers=["*"],  # Permitir todos os cabeçalhos.
)



# Registrar os routers
app.include_router(admin_router)
app.include_router(comentario_router)
app.include_router(denuncia_produto_router)
app.include_router(endereco_envio_router)
app.include_router(info_usuario_router)
app.include_router(mensagem_router)
app.include_router(pedido_router)
app.include_router(produto_router)
app.include_router(usuario_router)
app.include_router(pesquisa_router)

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.62", port=8000) 
