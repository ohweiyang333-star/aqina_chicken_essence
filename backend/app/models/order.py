"""Order models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class OrderItem(BaseModel):
    """Single item in an order."""

    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_name_zh: str = Field(..., description="Product name in Chinese")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Unit price in SGD")
    total_price: float = Field(..., ge=0, description="Total price for this item")


class CustomerInfo(BaseModel):
    """Customer information for an order."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    whatsapp: str = Field(..., min_length=8, max_length=20, description="WhatsApp phone number")
    address: str = Field(..., min_length=10, max_length=500)


class CreateOrderRequest(BaseModel):
    """Request model for creating a new order."""

    customer: CustomerInfo
    items: list[OrderItem] = Field(..., min_length=1, max_length=20)
    total_amount: float = Field(..., ge=0, description="Total order amount in SGD")
    payment_method: Literal["shopee", "paynow", "paylah"] = "shopee"
    notes: Optional[str] = Field(None, max_length=1000)


class OrderResponse(BaseModel):
    """Response model for order data."""

    order_id: str
    customer: CustomerInfo
    items: list[OrderItem]
    total_amount: float
    payment_method: str
    payment_status: Literal["pending", "paid", "failed", "refunded"]
    order_status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdateOrderStatusRequest(BaseModel):
    """Request model for updating order status."""

    order_status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    notes: Optional[str] = Field(None, max_length=1000)


class ListOrdersResponse(BaseModel):
    """Response model for listing orders."""

    orders: list[OrderResponse]
    total_count: int
    page: int
    page_size: int
