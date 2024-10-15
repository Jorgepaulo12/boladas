from controlers.mensagem import *
from schemas import *
from auth import *
from typing import List, Dict
from fastapi import APIRouter,HTTPException, WebSocket, WebSocketDisconnect
router=APIRouter(prefix="/menssagem",tags=["rotas de mensagem"])

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

manager = ConnectionManager()
@router.websocket("/ws/mensagens/{user_id}")
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

@router.put("/mensagens/{mensagem_id}")
def update_mensagem_endpoint(mensagem_id: int, mensagem: MensagemUpdate, db: Session = Depends(get_db)):
    db_mensagem = update_mensagem_db(db=db, mensagem_id=mensagem_id, mensagem=mensagem)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem


# Rotas HTTP para gerenciar mensagens
@router.post("/")
async def create_message(mensagem: MensagemCreate, db: Session = Depends(get_db)):
    # Cria a mensagem no banco de dados
    db_mensagem = create_mensagem_db(db, mensagem)
    
    # Envia a mensagem para o WebSocket do destinatário
    to_user_id = mensagem.destinatarioID
    message_content = mensagem.conteudo
    # Envio da mensagem via WebSocket
    await manager.send_private_message(message_content, to_user_id)

    return db_mensagem

@router.get("/{mensagem_id}")
def read_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = get_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem

@router.get("/{usuario1_id}/{usuario2_id}")
def get_conversas(usuario1_id: int, usuario2_id: int, db: Session = Depends(get_db)):
    conversas = get_conversas_entre_usuarios(db, usuario1_id, usuario2_id)
    return conversas

@router.delete("/mensagens/{mensagem_id}")
def delete_mensagem_endpoint(mensagem_id: int, db: Session = Depends(get_db)):
    db_mensagem = delete_mensagem(db=db, mensagem_id=mensagem_id)
    if db_mensagem is None:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return db_mensagem