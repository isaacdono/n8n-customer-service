from fastapi import APIRouter
from repositories.chat_repository import ChatRepository

router = APIRouter()

@router.get("/history/{user_id}")
async def get_user_history(user_id: str):
    """Recupera o histórico de chat de um usuário"""
    history = await ChatRepository.get_chat_history(user_id, limit=20)
    return {"user_id": user_id, "messages": history}

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Recupera estatísticas do usuário"""
    stats = await ChatRepository.get_user_stats(user_id)
    return {"user_id": user_id, "stats": stats}

@router.delete("/history/{user_id}")
async def delete_user_history(user_id: str):
    """Deleta todo o histórico de um usuário"""
    deleted = await ChatRepository.delete_user_history(user_id)
    return {"user_id": user_id, "deleted_messages": deleted, "status": "deleted"}
