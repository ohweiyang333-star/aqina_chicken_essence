"""Orders API endpoints."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from datetime import datetime
from typing import Optional
from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1 import Increment
import uuid

from app.api.deps import DB, Admin, PageParam, PageSizeParam, OrderFilters
from app.models.order import (
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
    ListOrdersResponse,
    OrderItem,
    CustomerInfo,
)
from app.services.storage_uploads import upload_public_file_to_firebase

router = APIRouter(prefix="/orders", tags=["Orders"])

LANDING_PACKAGES = {
    "pack1": {"name": "7天启动装", "name_en": "7-Day Starter Pack", "price": 39.9, "box_count": 1, "pack_count": 7},
    "pack2": {"name": "14天常备装", "name_en": "14-Day Care Pack", "price": 75.0, "box_count": 2, "pack_count": 14},
    "pack4": {"name": "28天月度装", "name_en": "28-Day Monthly Pack", "price": 149.0, "box_count": 4, "pack_count": 28},
    "pack6": {"name": "42天家庭装", "name_en": "42-Day Family Pack", "price": 219.0, "box_count": 6, "pack_count": 42},
}
ALLOWED_RECEIPT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_RECEIPT_BYTES = 8 * 1024 * 1024
SINGLE_BOX_SHIPPING_FEE = 8.0


def _shipping_fee_for(box_count: int) -> float:
    return 0.0 if box_count >= 2 else SINGLE_BOX_SHIPPING_FEE


def _money(value: float) -> float:
    return round(value + 1e-8, 2)


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


@router.post("/with-receipt", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_landing_order_with_receipt(
    db: DB,
    customer_name: str = Form(..., min_length=1, max_length=100),
    customer_phone: str = Form(..., min_length=8, max_length=20),
    customer_address: str = Form(..., min_length=10, max_length=500),
    product_id: str = Form(..., min_length=1, max_length=100),
    payment_receipt: UploadFile = File(...),
):
    """
    Create a landing-page PayNow order after receipt upload.

    Public endpoint - customers must submit a PayNow receipt image before the
    order enters the admin queue.
    """
    package = LANDING_PACKAGES.get(product_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown package")

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
    shipping_fee = _shipping_fee_for(box_count)
    total_amount = _money(subtotal_amount + shipping_fee)
    now = datetime.now()
    customer = {
        "name": customer_name,
        "email": None,
        "whatsapp": customer_phone,
        "address": customer_address,
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

    customer_id = f"customer_{customer_phone}"
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
                "name": customer_name,
                "email": None,
                "whatsapp": customer_phone,
                "address": customer_address,
                "total_spent": total_amount,
                "purchase_count": 1,
                "last_purchase_date": SERVER_TIMESTAMP,
                "customer_level": "new" if total_amount < 100 else "standard",
                "created_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP,
            }
        )

    return OrderResponse(
        order_id=order_id,
        customer=CustomerInfo(**customer),
        items=[OrderItem(**item)],
        subtotal_amount=subtotal_amount,
        shipping_fee=shipping_fee,
        box_count=box_count,
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

    # Prepare order document
    order_dict = {
        "customer": order_data.customer.model_dump(),
        "items": [item.model_dump() for item in order_data.items],
        "subtotal_amount": subtotal_amount,
        "shipping_fee": shipping_fee,
        "box_count": box_count,
        "total_amount": _money(subtotal_amount + shipping_fee),
        "payment_method": order_data.payment_method,
        "payment_status": "pending",
        "order_status": "pending",
        "payment_receipt_url": None,
        "notes": order_data.notes,
        "source": order_data.source,
        "marketing_contact_id": order_data.marketing_contact_id,
        "checkout_session_id": order_data.checkout_session_id,
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
