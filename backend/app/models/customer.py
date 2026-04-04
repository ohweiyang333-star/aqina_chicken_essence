"""Customer (CRM) models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class CustomerResponse(BaseModel):
    """Response model for customer data."""

    customer_id: str
    name: str
    email: str
    whatsapp: str
    address: Optional[str] = None
    total_spent: float = Field(default=0, ge=0)
    purchase_count: int = Field(default=0, ge=0)
    last_purchase_date: Optional[datetime] = None
    customer_level: Literal["new", "standard", "vip"] = "new"
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdateCustomerRequest(BaseModel):
    """Request model for updating customer information."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    whatsapp: Optional[str] = Field(None, min_length=8, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    customer_level: Optional[Literal["new", "standard", "vip"]] = None


class ListCustomersResponse(BaseModel):
    """Response model for listing customers."""

    customers: list[CustomerResponse]
    total_count: int
    page: int
    page_size: int
