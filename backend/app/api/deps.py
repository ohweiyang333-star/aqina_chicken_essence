"""Dependency injection utilities for API routes."""
from typing import Annotated, Optional
from fastapi import Query, Depends
from app.core.security import AdminUser, get_current_admin
from app.core.firebase import get_firestore
from google.cloud.firestore import Client as FirestoreClient


# Common query parameters for pagination
async def get_page(page: int = Query(ge=1, default=1, description="Page number")) -> int:
    return page


async def get_page_size(page_size: int = Query(ge=1, le=100, default=20, description="Items per page")) -> int:
    return page_size


PageParam = Annotated[int, Depends(get_page)]
PageSizeParam = Annotated[int, Depends(get_page_size)]


# Database dependency
def get_db() -> FirestoreClient:
    """Get Firestore database client."""
    return get_firestore()


DB = Annotated[FirestoreClient, Depends(get_db)]
Admin = Annotated[dict, Depends(get_current_admin)]


# Common filter parameters
class OrderFilterParams:
    """Common filter parameters for orders."""

    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


async def get_order_filters(
    status: Optional[str] = Query(None, description="Filter by order status"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
) -> OrderFilterParams:
    filters = OrderFilterParams()
    filters.status = status
    filters.start_date = start_date
    filters.end_date = end_date
    return filters


OrderFilters = Annotated[OrderFilterParams, Depends(get_order_filters)]
