from fastapi import APIRouter, Request
from models.schemas import InboundWhatsAppMsg
from services.chat_handler import ChatHandler
from services.whatsapp_service import WhatsAppService

router = APIRouter()

@router.post("/webhook/whatsapp")
async def receive_from_whatsapp(msg: InboundWhatsAppMsg):
    """Recebe a mensagem do wrapper wwebjs (Node.js) e toma a decisão"""
    result = await ChatHandler.process_incoming_message(msg)
    return result

@router.post("/send")
async def send_to_user(request: Request):
    """
    Endpoint em que o N8N vai bater quando quiser enviar resposta.
    O FastAPI repassa para o wwebjs.
    """
    data = await request.json()
    to = data.get("to")
    message = data.get("message")

    if not to or not message:
        return {"error": "Missing 'to' or 'message' fields"}

    await WhatsAppService.send_to_whatsapp(to, message)
    return {"status": "success", "info": "Mensagem enviada pro whatsapp-web.js"}
