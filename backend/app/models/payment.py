"""Payment models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
from datetime import datetime


class CreatePaymentRequest(BaseModel):
    """Request model for creating a new payment record."""

    order_id: str = Field(..., description="Associated order ID")
    method: Literal["paynow"] = Field(..., description="Payment method")
    amount: float = Field(..., ge=0, description="Payment amount in SGD")
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    screenshot_url: Optional[str] = Field(None, description="Payment screenshot URL")


class PaymentResponse(BaseModel):
    """Response model for payment data."""

    payment_id: str
    order_id: str
    method: str
    amount: float
    status: Literal["pending", "payment_submitted", "paid", "failed", "refunded"]
    transaction_id: Optional[str] = None
    screenshot_url: Optional[str] = None
    payment_verification: Optional[dict[str, Any]] = None
    risk_flags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdatePaymentStatusRequest(BaseModel):
    """Request model for updating payment status."""

    status: Literal["pending", "payment_submitted", "paid", "failed", "refunded"]
    transaction_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)


class ListPaymentsResponse(BaseModel):
    """Response model for listing payments."""

    payments: list[PaymentResponse]
    total_count: int
    page: int
    page_size: int
