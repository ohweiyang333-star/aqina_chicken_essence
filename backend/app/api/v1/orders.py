"""Orders API endpoints."""
from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime
from typing import Optional
from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1 import Increment

from app.api.deps import DB, Admin, PageParam, PageSizeParam, OrderFilters
from app.models.order import (
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
    ListOrdersResponse,
    OrderItem,
    CustomerInfo,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


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


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: CreateOrderRequest, db: DB):
    """
    Create a new order.

    Public endpoint - no authentication required for customer checkout.
    """
    # Generate order ID
    import uuid
    order_id = f"order_{uuid.uuid4().hex[:12]}"

    # Prepare order document
    order_dict = {
        "customer": order_data.customer.model_dump(),
        "items": [item.model_dump() for item in order_data.items],
        "total_amount": order_data.total_amount,
        "payment_method": order_data.payment_method,
        "payment_status": "pending",
        "order_status": "pending",
        "notes": order_data.notes,
        "created_at": SERVER_TIMESTAMP,
        "updated_at": SERVER_TIMESTAMP,
    }

    # Save to Firestore
    db.collection("orders").document(order_id).set(order_dict)

    # Also create/update customer record
    customer_id = f"customer_{order_data.customer.email}"
    customer_ref = db.collection("customers").document(customer_id)
    customer_doc = customer_ref.get()

    if customer_doc.exists:
        # Update existing customer
        customer_ref.update({
            "total_spent": Increment(order_data.total_amount),
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
            "total_spent": order_data.total_amount,
            "purchase_count": 1,
            "last_purchase_date": SERVER_TIMESTAMP,
            "customer_level": "new" if order_data.total_amount < 100 else "standard",
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
        customer_ref.set(customer_dict)

    # Return created order
    order_dict["order_id"] = order_id
    order_dict["created_at"] = datetime.now()  # For response
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
