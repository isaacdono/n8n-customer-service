from models.schemas import InboundWhatsAppMsg
from services.whatsapp_service import WhatsAppService
from services.n8n_service import N8NService
from core.config import settings

MENU_MSG = """👋 Olá! Bem-vindo ao meu portfólio de Agentes de IA.\n
Para testar, envie apenas "@clinica" ou "@restaurante". \n

*@clinica* -> Agente de clínica (Agendamentos no Calendar).
*@restaurante* -> Agente para pedidos e estoque.

A qualquer momento, digite *@fim* para encerrar a conversa atual, limpar o histórico e voltar a este menu."""

WELCOME_MESSAGES = {
    "@clinica": "👋 Olá! Sou a Ana, assistente virtual da clínica. Como posso ajudar você hoje? Você gostaria de agendar, remarcar ou cancelar uma consulta?",
    "@restaurante": "👋 Olá! Sou o Carlos, assistente virtual do restaurante. Como posso ajudar você? Gostaria de fazer um pedido ou consultar o estoque?",
}

# Dicionário para rastrear sessões ativas em memória
active_sessions = {}


class ChatHandler:
    @staticmethod
    async def process_incoming_message(msg: InboundWhatsAppMsg) -> dict:
        body = msg.body.strip()
        sender = msg.sender_id
        prefix_candidate = body.split(" ")[0].lower()

        # 1. Comando para encerrar a conversa atual
        if body.lower() in ["@fim", "/end"]:
            await N8NService.delete_user_history(sender)
            
            # Limpar sessão em memória
            if sender in active_sessions:
                del active_sessions[sender]
            
            # Enviar duas mensagens: confirmação + menu
            confirm_msg = "✅ Conversa encerrada e histórico limpo!"
            await WhatsAppService.send_to_whatsapp(sender, confirm_msg)
            await WhatsAppService.send_to_whatsapp(sender, MENU_MSG)
            return {"status": "session_ended", "user": sender}

        # 2. Verifica se o usuário já está em uma conversa ativa
        active_prefix = active_sessions.get(sender)
        
        if active_prefix:
            # Usuário já tem um prefixo ativo, usa a mensagem como está
            message_cleaned = body
        elif prefix_candidate in settings.n8n_webhooks:
            # Novo prefixo detectado
            active_prefix = prefix_candidate
            active_sessions[sender] = active_prefix
            welcome_msg = WELCOME_MESSAGES.get(active_prefix, "👋 Olá! Como posso ajudar?")
            await WhatsAppService.send_to_whatsapp(sender, welcome_msg)
            
            message_cleaned = body[len(active_prefix):].strip()
            
            # Se a mensagem está vazia (só o prefixo), não roteia para n8n
            if not message_cleaned:
                return {"status": "welcome_sent", "prefix": active_prefix}
        else:
            # 3. Se não tem sessão ativa e não enviou prefixo válido, mostra menu
            await WhatsAppService.send_to_whatsapp(sender, MENU_MSG)
            return {"status": "menu_sent"}

        n8n_url = settings.n8n_webhooks[active_prefix]
        
        payload_to_n8n = {
            "from": sender,
            "name": msg.sender_name,
            "original_message": body,
            "message_cleaned": message_cleaned,
            "prefix": active_prefix,
            "timestamp": msg.timestamp
        }

        await N8NService.route_to_n8n(n8n_url, active_prefix, payload_to_n8n)
        return {"status": "routed", "prefix": active_prefix}
