import httpx
from core.config import settings

class WhatsAppService:
    @staticmethod
    async def send_to_whatsapp(to: str, text: str):
        """Helper para enviar a resposta final pro Node.js enviar via WhatsApp"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(settings.WWEBJS_SEND_URL, json={"to": to, "message": text})
            except Exception as e:
                print(f"[Erro] Falha ao contatar gateway whatsapp-web.js: {e}")
