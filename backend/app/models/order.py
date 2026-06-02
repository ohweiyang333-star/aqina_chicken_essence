"""Order models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
from datetime import date, datetime


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
    email: Optional[str] = Field(None, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    whatsapp: str = Field(..., min_length=8, max_length=20, description="WhatsApp phone number")
    address: str = Field(..., min_length=10, max_length=500)


class GiftChoice(BaseModel):
    """Free French Poulet gift selected for the 2-box offer."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    weight: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=250)


class CreateOrderRequest(BaseModel):
    """Request model for creating a new order."""

    customer: CustomerInfo
    items: list[OrderItem] = Field(..., min_length=1, max_length=20)
    total_amount: float = Field(..., ge=0, description="Total order amount in SGD")
    payment_method: Literal["paynow"] = "paynow"
    gift_choice: Optional[Any] = None
    notes: Optional[str] = Field(None, max_length=1000)
    source: Optional[str] = Field(default="web_checkout", max_length=100)
    marketing_contact_id: Optional[str] = Field(default=None, max_length=200)
    conversation_id: Optional[str] = Field(default=None, max_length=200)
    channel: Optional[str] = Field(default=None, max_length=50)
    checkout_session_id: Optional[str] = Field(default=None, max_length=200)
    utm_source: Optional[str] = Field(default=None, max_length=200)
    utm_campaign: Optional[str] = Field(default=None, max_length=200)
    meta_campaign_id: Optional[str] = Field(default=None, max_length=200)
    meta_adset_id: Optional[str] = Field(default=None, max_length=200)
    meta_ad_id: Optional[str] = Field(default=None, max_length=200)


class OrderResponse(BaseModel):
    """Response model for order data."""

    order_id: str
    customer: CustomerInfo
    items: list[OrderItem]
    subtotal_amount: Optional[float] = None
    shipping_fee: float = 0
    box_count: int = 0
    gift_choice: Optional[GiftChoice] = None
    total_amount: float
    payment_method: str
    payment_status: Literal["pending", "payment_submitted", "paid", "failed", "refunded"]
    order_status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    payment_receipt_url: Optional[str] = None
    transaction_id: Optional[str] = None
    payment_verification: Optional[dict[str, Any]] = None
    risk_flags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    source: Optional[str] = None
    source_channel: Optional[str] = None
    marketing_contact_id: Optional[str] = None
    conversation_id: Optional[str] = None
    channel: Optional[str] = None
    checkout_session_id: Optional[str] = None
    created_from: Optional[str] = None
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None
    meta_campaign_id: Optional[str] = None
    meta_adset_id: Optional[str] = None
    meta_ad_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdateOrderStatusRequest(BaseModel):
    """Request model for updating order status."""

    order_status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    notes: Optional[str] = Field(None, max_length=1000)


class OrderContactTemplate(BaseModel):
    """Approved WhatsApp template available for order notifications."""

    name: str
    language_code: str = "en_US"
    category: Optional[str] = None


class OrderContactContextResponse(BaseModel):
    """Admin contact context for following up on an order."""

    order_id: str
    source_label: str
    source_channel: Optional[str] = None
    customer_name: str
    raw_whatsapp: str
    normalized_whatsapp: Optional[str] = None
    whatsapp_draft_url: Optional[str] = None
    contact_id: Optional[str] = None
    conversation_id: Optional[str] = None
    conversation_url: Optional[str] = None
    window_is_open: bool = False
    window_expires_at: Optional[datetime] = None
    backend_send_method: Optional[Literal["free_text", "template"]] = None
    approved_templates: list[OrderContactTemplate] = Field(default_factory=list)


class SendOrderWhatsAppNotificationRequest(BaseModel):
    """Admin request to send a WhatsApp order follow-up."""

    expected_ship_date: date
    message: str = Field(..., min_length=1, max_length=4096)
    template_name: Optional[str] = Field(None, min_length=1, max_length=512)
    language_code: str = Field(default="en_US", min_length=2, max_length=32)
    body_variables: list[str] = Field(default_factory=list)


class SendOrderWhatsAppNotificationResponse(BaseModel):
    """Result of sending a WhatsApp order follow-up."""

    status: Literal["sent"]
    method: Literal["free_text", "template"]
    order_id: str
    expected_ship_date: date
    conversation_id: str
    provider_message_id: Optional[str] = None
    message_id: Optional[str] = None


class ListOrdersResponse(BaseModel):
    """Response model for listing orders."""

    orders: list[OrderResponse]
    total_count: int
    page: int
    page_size: int
