from models.schemas import InboundWhatsAppMsg
from repositories.chat_repository import ChatRepository
from repositories.session_repository import SessionRepository
from services.whatsapp_service import WhatsAppService
from services.n8n_service import N8NService
from core.config import settings

MENU_MSG = """Olá! Bem-vindo ao gateway de atendimento automatizado.

Para iniciar, envie apenas "@clinica" ou "@restaurante":

*@clinica* -> Agendamento, remarcação e cancelamento de consultas (Google Calendar).
*@restaurante* -> Cardápio, pedidos e reservas de mesa (Google Sheets CRM).

A qualquer momento, digite *@fim* para encerrar a sessão atual, limpar o histórico e voltar a este menu."""

WELCOME_MESSAGES = {
    "@clinica": "Olá! Sou a Ana, assistente virtual da clínica. Como posso ajudar você hoje? Gostaria de agendar, remarcar ou cancelar uma consulta?",
    "@restaurante": "Olá! Sou o Carlos, assistente virtual do restaurante. Como posso ajudar você hoje? Gostaria de ver o cardápio, fazer um pedido ou reservar uma mesa?",
}

# Fallback in-memory dictionary if DB is temporarily unavailable
active_sessions = {}


class ChatHandler:
    @staticmethod
    async def _get_session(sender: str):
        try:
            db_prefix = await SessionRepository.get_active_session(sender)
            if db_prefix:
                active_sessions[sender] = db_prefix
                return db_prefix
        except Exception:
            pass
        return active_sessions.get(sender)

    @staticmethod
    async def _set_session(sender: str, prefix: str):
        active_sessions[sender] = prefix
        try:
            await SessionRepository.set_active_session(sender, prefix)
        except Exception:
            pass

    @staticmethod
    async def process_incoming_message(msg: InboundWhatsAppMsg) -> dict:
        body = msg.body.strip()
        sender = msg.sender_id
        prefix_candidate = body.split(" ")[0].lower()

        # 1. Command to end current conversation and clear memory
        if body.lower() in ["@fim", "/end"]:
            await N8NService.delete_user_history(sender)
            if sender in active_sessions:
                del active_sessions[sender]

            confirm_msg = "Conversa encerrada e histórico limpo."
            await WhatsAppService.send_to_whatsapp(sender, confirm_msg)
            await WhatsAppService.send_to_whatsapp(sender, MENU_MSG)
            return {"status": "session_ended", "user": sender}

        # 2. Check if user already has an active session in PostgreSQL / memory
        active_prefix = await ChatHandler._get_session(sender)

        if active_prefix:
            message_cleaned = body
        elif prefix_candidate in settings.n8n_webhooks:
            active_prefix = prefix_candidate
            await ChatHandler._set_session(sender, active_prefix)
            welcome_msg = WELCOME_MESSAGES.get(active_prefix, "Ola! Como posso ajudar?")
            await WhatsAppService.send_to_whatsapp(sender, welcome_msg)
            await N8NService.seed_welcome_in_memory(sender, msg.sender_name, active_prefix, welcome_msg)

            message_cleaned = body[len(active_prefix):].strip()
            if not message_cleaned:
                return {"status": "welcome_sent", "prefix": active_prefix}
        else:
            # 3. No active session and no valid prefix -> send menu
            await WhatsAppService.send_to_whatsapp(sender, MENU_MSG)
            return {"status": "menu_sent"}

        # Log telemetry in PostgreSQL
        try:
            await ChatRepository.save_message(
                user_id=sender,
                sender_name=msg.sender_name,
                prefix=active_prefix,
                user_message=message_cleaned,
                timestamp=msg.timestamp,
            )
        except Exception:
            pass

        n8n_url = settings.n8n_webhooks[active_prefix]
        payload_to_n8n = {
            "from": sender,
            "name": msg.sender_name,
            "original_message": message_cleaned,
            "message_cleaned": message_cleaned,
            "prefix": active_prefix,
            "timestamp": msg.timestamp,
        }

        await N8NService.route_to_n8n(n8n_url, active_prefix, payload_to_n8n)
        return {"status": "routed", "prefix": active_prefix}
