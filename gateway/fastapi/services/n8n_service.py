import httpx
import asyncpg
from core.config import settings

class N8NService:
    @staticmethod
    async def route_to_n8n(n8n_url: str, active_prefix: str, payload_to_n8n: dict) -> None:
        """Envia POST pro n8n de forma assíncrona"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(n8n_url, json=payload_to_n8n)
                print(f"[OK] Roteado para {active_prefix} (n8n)")
            except Exception as e:
                print(f"[Erro] n8n Webhook inacessível [{active_prefix}]: {e}")

    @staticmethod
    async def delete_user_history(user_id: str) -> None:
        """Deleta histórico do usuário na tabela chat_history"""
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL)
            await conn.execute(
                "DELETE FROM chat_history WHERE session_id = $1",
                user_id
            )
            await conn.close()
            print(f"[OK] Histórico deletado para {user_id} (chat_history)")
        except Exception as e:
            print(f"[Erro] Falha ao deletar histórico: {e}")
