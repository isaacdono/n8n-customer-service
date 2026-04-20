from pydantic import BaseModel

class InboundWhatsAppMsg(BaseModel):
    sender_id: str
    body: str
    sender_name: str
    timestamp: int

class OutboundWhatsAppMsg(BaseModel):
    to: str
    message: str
