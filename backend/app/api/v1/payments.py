"""Payments API endpoints."""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from google.cloud.firestore import SERVER_TIMESTAMP

from app.api.deps import DB, Admin, PageParam, PageSizeParam
from app.models.payment import (
    CreatePaymentRequest,
    PaymentResponse,
    UpdatePaymentStatusRequest,
    ListPaymentsResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=ListPaymentsResponse)
async def list_payments(
    db: DB,
    admin: Admin,
    page: PageParam,
    page_size: PageSizeParam,
):
    """
    Get all payment records.

    Requires admin authentication.
    """
    # Build query
    query = db.collection("payments").order_by("created_at", direction="DESCENDING")

    # Get all payments
    docs = query.stream()

    payments = []
    for doc in docs:
        payment_data = doc.to_dict()
        payment_data["payment_id"] = doc.id
        payment_data["created_at"] = payment_data.get("created_at", datetime.now())
        payments.append(PaymentResponse(**payment_data))

    # Apply pagination
    total_count = len(payments)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_payments = payments[start_idx:end_idx]

    return ListPaymentsResponse(
        payments=paginated_payments,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: DB, admin: Admin):
    """
    Get a specific payment by ID.

    Requires admin authentication.
    """
    doc = db.collection("payments").document(payment_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    payment_data = doc.to_dict()
    payment_data["payment_id"] = doc.id
    payment_data["created_at"] = payment_data.get("created_at", datetime.now())

    return PaymentResponse(**payment_data)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: CreatePaymentRequest, db: DB, admin: Admin):
    """
    Create a new payment record.

    Requires admin authentication.
    """
    # Generate payment ID
    import uuid
    payment_id = f"payment_{uuid.uuid4().hex[:12]}"

    # Prepare payment document
    payment_dict = {
        "order_id": payment_data.order_id,
        "method": payment_data.method,
        "amount": payment_data.amount,
        "status": "pending",
        "transaction_id": payment_data.transaction_id,
        "screenshot_url": payment_data.screenshot_url,
        "created_at": SERVER_TIMESTAMP,
        "updated_at": SERVER_TIMESTAMP,
    }

    # Save to Firestore
    db.collection("payments").document(payment_id).set(payment_dict)

    # Also update order payment status
    order_ref = db.collection("orders").document(payment_data.order_id)
    order_ref.update({
        "payment_status": "pending",
        "updated_at": SERVER_TIMESTAMP,
    })

    # Return created payment
    payment_dict["payment_id"] = payment_id
    payment_dict["created_at"] = datetime.now()

    return PaymentResponse(**payment_dict)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: str,
    update_data: UpdatePaymentStatusRequest,
    db: DB,
    admin: Admin,
):
    """
    Update payment status.

    Requires admin authentication.
    """
    doc = db.collection("payments").document(payment_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Update payment
    update_dict = {
        "status": update_data.status,
        "updated_at": SERVER_TIMESTAMP,
    }

    if update_data.transaction_id:
        update_dict["transaction_id"] = update_data.transaction_id

    if update_data.notes:
        update_dict["notes"] = update_data.notes

    db.collection("payments").document(payment_id).update(update_dict)

    # Also update order payment status
    payment_doc = db.collection("payments").document(payment_id).get()
    order_id = payment_doc.get("order_id")

    if order_id:
        db.collection("orders").document(order_id).update({
            "payment_status": update_data.status,
            "updated_at": SERVER_TIMESTAMP,
        })

    # Get updated payment
    updated_doc = db.collection("payments").document(payment_id).get()
    payment_data = updated_doc.to_dict()
    payment_data["payment_id"] = payment_id
    payment_data["created_at"] = payment_data.get("created_at", datetime.now())

    return PaymentResponse(**payment_data)
