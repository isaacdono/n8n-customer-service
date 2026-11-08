import json
import httpx
from core.database import Database


class N8NService:
    @staticmethod
    async def route_to_n8n(n8n_url: str, active_prefix: str, payload_to_n8n: dict) -> None:
        """Dispatches the incoming WhatsApp payload asynchronously to the target n8n webhook."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(n8n_url, json=payload_to_n8n)
                print(f"[OK] Routed to {active_prefix} (n8n)")
            except Exception as e:
                print(f"[Error] n8n webhook unreachable [{active_prefix}]: {e}")

    @staticmethod
    async def seed_welcome_in_memory(user_id: str, sender_name: str, prefix: str, welcome_msg: str) -> None:
        """Seeds the initial greeting into PostgreSQL chat_history so n8n memory knows the user was already greeted."""
        try:
            pool = Database.get_pool()
            ai_msg_json = json.dumps({"type": "ai", "data": {"content": welcome_msg, "additional_kwargs": {}, "response_metadata": {}}})
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO chat_history (session_id, user_id, sender_name, prefix, user_message, agent_response, message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                    """,
                    user_id,
                    user_id,
                    sender_name,
                    prefix,
                    prefix,
                    welcome_msg,
                    ai_msg_json,
                )
        except Exception as e:
            print(f"[Warn] Failed to seed welcome message in PostgreSQL: {e}")

    @staticmethod
    async def delete_user_history(user_id: str) -> None:
        """Clears both n8n session memory and FastAPI telemetry for a user in PostgreSQL."""
        try:
            pool = Database.get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM chat_history WHERE session_id = $1 OR user_id = $1",
                    user_id,
                )
                await conn.execute(
                    "DELETE FROM active_sessions WHERE user_id = $1",
                    user_id,
                )
            print(f"[OK] History and active session cleared for {user_id}")
        except Exception as e:
            print(f"[Error] Failed to clear user history: {e}")
