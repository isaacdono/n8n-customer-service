from fastapi import APIRouter
from api.routes import webhook, admin

api_router = APIRouter()

api_router.include_router(webhook.router, tags=["Webhook"])
api_router.include_router(admin.router, tags=["Admin"])
