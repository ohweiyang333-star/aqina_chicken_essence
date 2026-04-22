"""Pydantic models for API requests and responses."""
from app.models.order import (
    OrderItem,
    CustomerInfo,
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
    ListOrdersResponse,
)
from app.models.payment import (
    CreatePaymentRequest,
    PaymentResponse,
    UpdatePaymentStatusRequest,
    ListPaymentsResponse,
)
from app.models.customer import (
    CustomerResponse,
    UpdateCustomerRequest,
    ListCustomersResponse,
)
from app.models.chatbot import (
    FAQItem,
    ChatbotPackage,
    KnowledgeBase,
    PaymentSettings,
    EscalationSettings,
    ChatbotSettingsResponse,
    UpdateChatbotSettingsRequest,
    SalesConversationTurn,
    FollowUpTurnResult,
    EscalationRecord,
    CheckoutSessionResponse,
)
from app.models.marketing import (
    ProcessMarketingEventRequest,
    ProcessFollowUpJobRequest,
    ReconcileDueJobsRequest,
    NormalizedMarketingEvent,
)

__all__ = [
    # Order models
    "OrderItem",
    "CustomerInfo",
    "CreateOrderRequest",
    "OrderResponse",
    "UpdateOrderStatusRequest",
    "ListOrdersResponse",
    # Payment models
    "CreatePaymentRequest",
    "PaymentResponse",
    "UpdatePaymentStatusRequest",
    "ListPaymentsResponse",
    # Customer models
    "CustomerResponse",
    "UpdateCustomerRequest",
    "ListCustomersResponse",
    # Chatbot models
    "FAQItem",
    "ChatbotPackage",
    "KnowledgeBase",
    "PaymentSettings",
    "EscalationSettings",
    "ChatbotSettingsResponse",
    "UpdateChatbotSettingsRequest",
    "SalesConversationTurn",
    "FollowUpTurnResult",
    "EscalationRecord",
    "CheckoutSessionResponse",
    # Marketing models
    "ProcessMarketingEventRequest",
    "ProcessFollowUpJobRequest",
    "ReconcileDueJobsRequest",
    "NormalizedMarketingEvent",
]
