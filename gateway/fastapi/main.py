import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx

app = FastAPI()

# Definições de ambiente
WWEBJS_SEND_URL = os.getenv("WWEBJS_SEND_URL", "http://wwebjs-service:3000/send")

# Webhooks do n8n (pode configurar no docker-compose e apontar pro ip do host ou VM)
N8N_WEBHOOKS = {
    "@fala": os.getenv("N8N_FALA", "http://n8n-container:5678/webhook/fala"),
    "@clinica": os.getenv("N8N_CLINICA", "http://n8n-container:5678/webhook/clinica"),
    "@restaurante": os.getenv("N8N_RESTAURANTE", "http://n8n-container:5678/webhook/restaurante"),
}

class InboundWhatsAppMsg(BaseModel):
    sender_id: str
    body: str
    sender_name: str
    timestamp: int

class OutboundWhatsAppMsg(BaseModel):
    to: str
    message: str

# Estado em memória para rastrear em qual agente o usuário está logado (MVP)
# Em produção, para múltiplos workers, seria ideal usar Redis ou banco de dados.
active_sessions = {}

MENU_MSG = """👋 Olá! Bem-vindo ao meu portfólio de Agentes de IA.
Para testar, envie apenas o prefixo do agente desejado, ou já com a sua mensagem:

*@fala* -> Assistente de comunicação e PDF.
*@clinica* -> Agente de clínica (Agendamentos no Calendar).
*@restaurante* -> Agente para pedidos e estoque.

A qualquer momento, digite *@fim* para encerrar a conversa atual, limpar o histórico e voltar a este menu."""

async def send_to_whatsapp(to: str, text: str):
    """ Helper para enviar a resposta final pro Node.js enviar via WhatsApp """
    async with httpx.AsyncClient() as client:
        try:
            await client.post(WWEBJS_SEND_URL, json={"to": to, "message": text})
        except Exception as e:
            print(f"[Erro] Falha ao contatar gateway whatsapp-web.js: {e}")

@app.post("/webhook/whatsapp")
async def receive_from_whatsapp(msg: InboundWhatsAppMsg):
    """ Recebe a mensagem do wrapper wwebjs (Node.js) e toma a decisão """
    body = msg.body.strip()
    sender = msg.sender_id
    prefix_candidate = body.split(" ")[0].lower()

    # 1. Comando para encerrar a conversa atual
    if body.lower() == "@fim":
        if sender in active_sessions:
            del active_sessions[sender]
        # Informa ao usuário e também manda o menu para ele escolher novamente
        reset_msg = "✅ Conversa encerrada e histórico limpo!\n\n" + MENU_MSG
        await send_to_whatsapp(sender, reset_msg)
        return {"status": "session_ended"}

    # 2. Verifica se o usuário já tem uma conversa ativa com algum agente
    if sender in active_sessions:
        active_prefix = active_sessions[sender]
        # Toda a mensagem original é conteúdo para o agente
        message_cleaned = body 
    else:
        # 3. Se não tem sessão, verifica se enviou um prefixo válido para iniciar
        if prefix_candidate in N8N_WEBHOOKS:
            active_prefix = prefix_candidate
            active_sessions[sender] = active_prefix
            # O primeiro conteúdo tira o prefixo
            message_cleaned = body[len(active_prefix):].strip()
        else:
            # Sem sessão e sem prefixo válido -> envia menu
            await send_to_whatsapp(sender, MENU_MSG)
            return {"status": "menu_sent"}

    # Tendo o prefixo com certeza definido, mandamos ao n8n
    n8n_url = N8N_WEBHOOKS[active_prefix]
    
    # Preparando payload completo para o n8n Processar
    payload_to_n8n = {
        "from": sender,
        "name": msg.sender_name,
        "original_message": body,
        "message_cleaned": message_cleaned,
        "prefix": active_prefix,
        "timestamp": msg.timestamp
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Envia POST pro n8n de forma assíncrona
            await client.post(n8n_url, json=payload_to_n8n)
            print(f"[OK] Roteado para {active_prefix} (n8n)")
        except Exception as e:
            print(f"[Erro] n8n Webhook inacessível [{active_prefix}]: {e}")
            await send_to_whatsapp(sender, "Desculpe, este agente está temporariamente fora do ar.")

    return {"status": "routed", "agent": active_prefix}

@app.post("/send")
async def send_to_user(request: Request):
    """
    Endpoint em que o N8N vai bater quando quiser enviar resposta.
    Exemplo de payload do N8N: {"to": "5511999999999@c.us", "message": "Sua consulta foi agendada!"}
    O FastAPI repassa para o wwebjs (Node.js).
    """
    data = await request.json()
    to = data.get("to")
    message = data.get("message")

    if not to or not message:
        return {"error": "Missing 'to' or 'message' fields"}

    await send_to_whatsapp(to, message)
    return {"status": "success", "info": "Mensagem enviada pro whatsapp-web.js"}