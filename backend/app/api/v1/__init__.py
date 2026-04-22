"""API v1 endpoints."""
from fastapi import APIRouter
from app.api.v1 import auth, orders, payments, chatbot, customers, marketing

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(chatbot.router)
api_router.include_router(customers.router)
api_router.include_router(marketing.router)

__all__ = ["api_router"]
