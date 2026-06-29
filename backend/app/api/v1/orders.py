"""Orders API endpoints."""
import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile, status
from datetime import datetime
from typing import Optional
from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1 import Increment
import uuid

from app.api.deps import DB, Admin, PageParam, PageSizeParam, OrderFilters
from app.models.order import (
    CreateOrderRequest,
    OrderContactContextResponse,
    SendOrderWhatsAppNotificationRequest,
    SendOrderWhatsAppNotificationResponse,
    OrderResponse,
    UpdateOrderStatusRequest,
    ListOrdersResponse,
    OrderItem,
    CustomerInfo,
)
from app.services.marketing_contacts import MarketingContactService
from app.services.meta_conversions import MetaAddToCartEventInput, MetaConversionsService
from app.services.meta_client import get_meta_client
from app.services.gift_choices import normalize_gift_choice
from app.services.storage_uploads import upload_public_file_to_firebase
from app.services.task_queue import get_task_queue_service
from app.services.whatsapp_console import WhatsAppConsoleService

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)

LANDING_PACKAGES = {
    "pack1": {"name": "7天启动装", "name_en": "7-Day Starter Pack", "price": 47.9, "box_count": 1, "pack_count": 7},
    "pack2": {"name": "14天常备装", "name_en": "14-Day Care Pack", "price": 79.8, "box_count": 2, "pack_count": 14},
}
ALLOWED_RECEIPT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_RECEIPT_BYTES = 8 * 1024 * 1024
SINGLE_BOX_SHIPPING_FEE = 0.0


def _shipping_fee_for(box_count: int) -> float:
    return 0.0 if box_count >= 2 else SINGLE_BOX_SHIPPING_FEE


def _landing_receipt_shipping_fee_for(box_count: int) -> float:
    """Offer-reset landing receipt checkout uses the visible package total."""
    del box_count
    return 0.0


def _money(value: float) -> float:
    return round(value + 1e-8, 2)


def _gift_choice_for_package(product_id: str, value) -> dict[str, str] | None:
    if product_id != "pack2":
        return None
    return normalize_gift_choice(value)


def _normalize_customer_phone(customer_phone: str) -> str:
    normalized_phone = "".join(char for char in customer_phone if char.isdigit())
    if not 8 <= len(normalized_phone) <= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp phone must contain 8 to 20 digits",
        )
    return normalized_phone


def _normalize_customer_address(customer_address: str) -> str:
    normalized_address = customer_address.strip()
    if not 10 <= len(normalized_address) <= 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery address must be 10 to 500 characters",
        )
    return normalized_address


@router.get("", response_model=ListOrdersResponse)
async def list_orders(
    db: DB,
    admin: Admin,
    page: PageParam,
    page_size: PageSizeParam,
    filters: OrderFilters,
):
    """
    Get all orders with optional filtering.

    Requires admin authentication.
    """
    # Build query
    query = db.collection("orders").order_by("created_at", direction="DESCENDING")

    # Apply filters if provided
    if filters.status:
        query = query.where("order_status", "==", filters.status)

    # Get all matching orders (pagination in memory for simplicity)
    # In production, use cursor-based pagination
    docs = query.stream()

    orders = []
    for doc in docs:
        order_data = doc.to_dict()
        order_data["order_id"] = doc.id
        order_data["created_at"] = order_data.get("created_at", datetime.now())

        # Convert items to OrderItem models
        items_data = order_data.get("items", [])
        order_data["items"] = [
            OrderItem(**item) if isinstance(item, dict) else item
            for item in items_data
        ]

        # Convert customer to CustomerInfo model
        customer_data = order_data.get("customer", {})
        order_data["customer"] = (
            CustomerInfo(**customer_data) if isinstance(customer_data, dict) else customer_data
        )

        orders.append(OrderResponse(**order_data))

    # Apply pagination
    total_count = len(orders)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_orders = orders[start_idx:end_idx]

    return ListOrdersResponse(
        orders=paginated_orders,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}/contact-context", response_model=OrderContactContextResponse)
async def get_order_contact_context(order_id: str, db: DB, admin: Admin):
    """
    Get WhatsApp follow-up context for an order.

    Requires admin authentication.
    """
    del admin
    try:
        return _build_whatsapp_console(db).order_contact_context(order_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{order_id}/whatsapp-notifications", response_model=SendOrderWhatsAppNotificationResponse)
async def send_order_whatsapp_notification(
    order_id: str,
    body: SendOrderWhatsAppNotificationRequest,
    db: DB,
    admin: Admin,
):
    """
    Send a WhatsApp order notification from the admin order dashboard.

    Uses free-form text only while the customer service window is open. When
    the window is closed, an approved WhatsApp template must be selected.
    """
    try:
        return _build_whatsapp_console(db).send_order_notification(
            order_id,
            expected_ship_date=body.expected_ship_date,
            message=body.message,
            template_name=body.template_name,
            language_code=body.language_code,
            body_variables=body.body_variables,
            admin=admin,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: DB, admin: Admin):
    """
    Get a specific order by ID.

    Requires admin authentication.
    """
    doc = db.collection("orders").document(order_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order_data = doc.to_dict()
    order_data["order_id"] = doc.id

    # Convert items and customer
    items_data = order_data.get("items", [])
    order_data["items"] = [
        OrderItem(**item) if isinstance(item, dict) else item
        for item in items_data
    ]
    customer_data = order_data.get("customer", {})
    order_data["customer"] = (
        CustomerInfo(**customer_data) if isinstance(customer_data, dict) else customer_data
    )

    return OrderResponse(**order_data)


def _build_whatsapp_console(db) -> WhatsAppConsoleService:
    return WhatsAppConsoleService(
        db=db,
        task_queue=get_task_queue_service(),
        contact_service=MarketingContactService(db),
        meta_client=get_meta_client(),
    )


@router.post("/with-receipt", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_landing_order_with_receipt(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DB,
    customer_name: str = Form(..., min_length=1, max_length=100),
    customer_phone: str = Form(...),
    customer_address: str = Form(...),
    product_id: str = Form(..., min_length=1, max_length=100),
    payment_receipt: UploadFile = File(...),
    gift_choice: Optional[str] = Form(default=None, max_length=250),
    marketing_consent: Optional[str] = Form(default=None, max_length=20),
    marketing_event_id: Optional[str] = Form(default=None, max_length=160),
    event_source_url: Optional[str] = Form(default=None, max_length=1000),
    page_path: Optional[str] = Form(default=None, max_length=200),
    landing_version: Optional[str] = Form(default=None, max_length=20),
    language: Optional[str] = Form(default=None, max_length=10),
    marketing_fbp: Optional[str] = Form(default=None, max_length=250),
    marketing_fbc: Optional[str] = Form(default=None, max_length=500),
):
    """
    Create a landing-page PayNow order after receipt upload.

    Public endpoint - customers must submit a PayNow receipt image before the
    order enters the admin queue.
    """
    package = LANDING_PACKAGES.get(product_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown package")

    normalized_name = customer_name.strip()
    if not normalized_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer name is required")
    normalized_phone = _normalize_customer_phone(customer_phone)
    normalized_address = _normalize_customer_address(customer_address)

    content_type = (payment_receipt.content_type or "").lower()
    if content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt must be JPG, PNG, or WebP")

    receipt_bytes = await payment_receipt.read()
    if not receipt_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt file is empty")
    if len(receipt_bytes) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Receipt file is too large")

    order_id = f"order_{uuid.uuid4().hex[:12]}"
    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }[content_type]
    receipt_url = upload_public_file_to_firebase(
        data=receipt_bytes,
        destination_path=f"payment_receipts/{order_id}/receipt.{extension}",
        content_type=content_type,
    )

    subtotal_amount = _money(float(package["price"]))
    box_count = int(package["box_count"])
    shipping_fee = _landing_receipt_shipping_fee_for(box_count)
    total_amount = _money(subtotal_amount + shipping_fee)
    normalized_gift_choice = _gift_choice_for_package(product_id, gift_choice)
    now = datetime.now()
    customer = {
        "name": normalized_name,
        "email": None,
        "whatsapp": normalized_phone,
        "address": normalized_address,
    }
    item = {
        "product_id": product_id,
        "product_name": package["name_en"],
        "product_name_zh": package["name"],
        "quantity": 1,
        "unit_price": subtotal_amount,
        "total_price": subtotal_amount,
    }
    order_dict = {
        "customer": customer,
        "items": [item],
        "subtotal_amount": subtotal_amount,
        "shipping_fee": shipping_fee,
        "box_count": box_count,
        "gift_choice": normalized_gift_choice,
        "total_amount": total_amount,
        "payment_method": "paynow",
        "payment_status": "payment_submitted",
        "order_status": "pending",
        "payment_receipt_url": receipt_url,
        "source": "landing_page",
        "marketing_contact_id": None,
        "checkout_session_id": None,
        "created_at": SERVER_TIMESTAMP,
        "updated_at": SERVER_TIMESTAMP,
    }
    db.collection("orders").document(order_id).set(order_dict)

    payment_id = f"payment_{uuid.uuid4().hex[:12]}"
    db.collection("payments").document(payment_id).set(
        {
            "order_id": order_id,
            "method": "paynow",
            "payment_method": "paynow",
            "amount": total_amount,
            "status": "payment_submitted",
            "transaction_id": None,
            "screenshot_url": receipt_url,
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
    )

    customer_id = f"customer_{normalized_phone}"
    customer_ref = db.collection("customers").document(customer_id)
    customer_doc = customer_ref.get()
    if customer_doc.exists:
        customer_ref.update({
            "total_spent": Increment(total_amount),
            "purchase_count": Increment(1),
            "last_purchase_date": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        })
    else:
        customer_ref.set(
            {
                "customer_id": customer_id,
                "name": normalized_name,
                "email": None,
                "whatsapp": normalized_phone,
                "address": normalized_address,
                "total_spent": total_amount,
                "purchase_count": 1,
                "last_purchase_date": SERVER_TIMESTAMP,
                "customer_level": "new" if total_amount < 100 else "standard",
                "created_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP,
            }
        )

    background_tasks.add_task(
        _send_meta_receipt_add_to_cart_event,
        db=db,
        order_id=order_id,
        event_input=MetaAddToCartEventInput(
            order_id=order_id,
            product_id=product_id,
            product_name=str(package["name_en"]),
            value=total_amount,
            customer_name=normalized_name,
            customer_phone=normalized_phone,
            quantity=1,
            marketing_consent=marketing_consent,
            event_id=marketing_event_id,
            event_source_url=event_source_url,
            page_path=page_path,
            landing_version=landing_version,
            language=language,
            fbp=marketing_fbp,
            fbc=marketing_fbc,
            client_ip_address=_client_ip_address(request),
            client_user_agent=request.headers.get("user-agent"),
        ),
    )

    return OrderResponse(
        order_id=order_id,
        customer=CustomerInfo(**customer),
        items=[OrderItem(**item)],
        subtotal_amount=subtotal_amount,
        shipping_fee=shipping_fee,
        box_count=box_count,
        gift_choice=normalized_gift_choice,
        total_amount=total_amount,
        payment_method="paynow",
        payment_status="payment_submitted",
        order_status="pending",
        payment_receipt_url=receipt_url,
        source="landing_page",
        marketing_contact_id=None,
        checkout_session_id=None,
        created_at=now,
        updated_at=now,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: CreateOrderRequest, db: DB):
    """
    Create a new order.

    Public endpoint - no authentication required for customer checkout.
    """
    # Generate order ID
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    subtotal_amount = _money(sum(item.total_price for item in order_data.items))
    box_count = sum(
        1 if item.product_id == "pack1" else 2 if item.product_id == "pack2" else 4 if item.product_id == "pack4" else 6 if item.product_id == "pack6" else item.quantity
        for item in order_data.items
    )
    shipping_fee = _shipping_fee_for(box_count)
    normalized_gift_choice = None
    for item in order_data.items:
        normalized_gift_choice = _gift_choice_for_package(item.product_id, order_data.gift_choice)
        if normalized_gift_choice:
            break
    has_marketing_attribution = bool(
        order_data.marketing_contact_id or order_data.conversation_id or order_data.channel
    )
    order_source = (
        "marketing_inbox"
        if has_marketing_attribution and (not order_data.source or order_data.source == "web_checkout")
        else order_data.source
    )

    # Prepare order document
    order_dict = {
        "customer": order_data.customer.model_dump(),
        "items": [item.model_dump() for item in order_data.items],
        "subtotal_amount": subtotal_amount,
        "shipping_fee": shipping_fee,
        "box_count": box_count,
        "gift_choice": normalized_gift_choice,
        "total_amount": _money(subtotal_amount + shipping_fee),
        "payment_method": order_data.payment_method,
        "payment_status": "pending",
        "order_status": "pending",
        "payment_receipt_url": None,
        "notes": order_data.notes,
        "source": order_source,
        "created_from": "marketing_inbox" if has_marketing_attribution else order_source,
        "marketing_contact_id": order_data.marketing_contact_id,
        "conversation_id": order_data.conversation_id,
        "channel": order_data.channel,
        "source_channel": order_data.channel,
        "checkout_session_id": order_data.checkout_session_id,
        "utm_source": order_data.utm_source,
        "utm_campaign": order_data.utm_campaign,
        "meta_campaign_id": order_data.meta_campaign_id,
        "meta_adset_id": order_data.meta_adset_id,
        "meta_ad_id": order_data.meta_ad_id,
        "created_at": SERVER_TIMESTAMP,
        "updated_at": SERVER_TIMESTAMP,
    }

    # Save to Firestore
    db.collection("orders").document(order_id).set(order_dict)

    # Also create/update customer record
    customer_seed = order_data.customer.email or order_data.customer.whatsapp
    customer_id = f"customer_{customer_seed}"
    customer_ref = db.collection("customers").document(customer_id)
    customer_doc = customer_ref.get()

    if customer_doc.exists:
        # Update existing customer
        customer_ref.update({
            "total_spent": Increment(order_dict["total_amount"]),
            "purchase_count": Increment(1),
            "last_purchase_date": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        })
    else:
        # Create new customer
        customer_dict = {
            "customer_id": customer_id,
            "name": order_data.customer.name,
            "email": order_data.customer.email,
            "whatsapp": order_data.customer.whatsapp,
            "address": order_data.customer.address,
            "total_spent": order_dict["total_amount"],
            "purchase_count": 1,
            "last_purchase_date": SERVER_TIMESTAMP,
            "customer_level": "new" if order_dict["total_amount"] < 100 else "standard",
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
        customer_ref.set(customer_dict)

    # Return created order
    now = datetime.now()
    order_dict["order_id"] = order_id
    order_dict["created_at"] = now  # For response
    order_dict["updated_at"] = now
    order_dict["customer"] = order_data.customer
    order_dict["items"] = order_data.items

    return OrderResponse(**order_dict)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    update_data: UpdateOrderStatusRequest,
    db: DB,
    admin: Admin,
):
    """
    Update order status.

    Requires admin authentication.
    """
    doc = db.collection("orders").document(order_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Update order
    update_dict = {
        "order_status": update_data.order_status,
        "updated_at": SERVER_TIMESTAMP,
    }

    if update_data.notes:
        update_dict["notes"] = update_data.notes

    db.collection("orders").document(order_id).update(update_dict)

    # Get updated order
    updated_doc = db.collection("orders").document(order_id).get()
    order_data = updated_doc.to_dict()
    order_data["order_id"] = order_id

    # Convert items and customer
    items_data = order_data.get("items", [])
    order_data["items"] = [
        OrderItem(**item) if isinstance(item, dict) else item
        for item in items_data
    ]
    customer_data = order_data.get("customer", {})
    order_data["customer"] = (
        CustomerInfo(**customer_data) if isinstance(customer_data, dict) else customer_data
    )

    return OrderResponse(**order_data)


@router.post("/{order_id}/track-purchase")
async def track_order_purchase(order_id: str, db: DB, admin: Admin):
    """Fire a Meta Purchase CAPI event for a confirmed-paid order (idempotent, best-effort).

    Called by admin after marking an order paid so Meta's optimizer learns what a real buyer
    looks like and the order is attributable. Never fails the request on CAPI errors — the
    paid status is already persisted client-side.
    """
    doc = db.collection("orders").document(order_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order = doc.to_dict()
    existing = order.get("meta_capi") if isinstance(order.get("meta_capi"), dict) else {}
    existing_purchase = existing.get("purchase") if isinstance(existing.get("purchase"), dict) else None
    if existing_purchase and existing_purchase.get("status") == "sent":
        return {"status": "already_sent", "order_id": order_id, "event_id": existing_purchase.get("event_id")}

    items = order.get("items") or []
    first_item = items[0] if items and isinstance(items[0], dict) else {}
    product_id = str(first_item.get("product_id") or first_item.get("product_name") or "aqina_order")
    product_name = str(first_item.get("product_name") or first_item.get("product_name_zh") or "Aqina")
    customer = order.get("customer") if isinstance(order.get("customer"), dict) else {}

    event_input = MetaAddToCartEventInput(
        order_id=order_id,
        product_id=product_id,
        product_name=product_name,
        value=float(order.get("total_amount") or 0.0),
        customer_name=str(customer.get("name") or ""),
        customer_phone=str(customer.get("whatsapp") or customer.get("phone") or ""),
        currency="SGD",
        quantity=int(order.get("box_count") or 1),
        marketing_consent=order.get("marketing_consent"),
        event_id=f"{order_id}_purchase",
    )
    result = MetaConversionsService(meta_client=get_meta_client()).send_purchase(event_input)

    update = {"meta_capi": {**existing, "purchase": result}, "updated_at": SERVER_TIMESTAMP}
    if not order.get("paid_at"):
        update["paid_at"] = SERVER_TIMESTAMP
    try:
        db.collection("orders").document(order_id).set(update, merge=True)
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.warning("purchase_capi_status_write_failed order_id=%s error=%s", order_id, exc)

    return {"status": result.get("status"), "order_id": order_id, "event_id": result.get("event_id")}


def _send_meta_receipt_add_to_cart_event(
    *,
    db,
    order_id: str,
    event_input: MetaAddToCartEventInput,
) -> None:
    result = MetaConversionsService(meta_client=get_meta_client()).send_add_to_cart(event_input)
    if result.get("status") == "skipped":
        return

    try:
        db.collection("orders").document(order_id).set(
            {
                "meta_capi": {
                    "add_to_cart": result,
                },
                "updated_at": SERVER_TIMESTAMP,
            },
            merge=True,
        )
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.warning("meta_capi_status_write_failed order_id=%s error=%s", order_id, exc)


def _client_ip_address(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else None
