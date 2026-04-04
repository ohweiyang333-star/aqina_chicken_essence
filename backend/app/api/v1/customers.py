"""Customers (CRM) API endpoints."""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from google.cloud.firestore import SERVER_TIMESTAMP

from app.api.deps import DB, Admin, PageParam, PageSizeParam
from app.models.customer import (
    CustomerResponse,
    UpdateCustomerRequest,
    ListCustomersResponse,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=ListCustomersResponse)
async def list_customers(
    db: DB,
    admin: Admin,
    page: PageParam,
    page_size: PageSizeParam,
):
    """
    Get all customer records.

    Requires admin authentication.
    """
    # Build query
    query = db.collection("customers").order_by("created_at", direction="DESCENDING")

    # Get all customers
    docs = query.stream()

    customers = []
    for doc in docs:
        customer_data = doc.to_dict()
        customer_data["customer_id"] = doc.id
        customer_data["created_at"] = customer_data.get("created_at", datetime.now())
        customers.append(CustomerResponse(**customer_data))

    # Apply pagination
    total_count = len(customers)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_customers = customers[start_idx:end_idx]

    return ListCustomersResponse(
        customers=paginated_customers,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: DB, admin: Admin):
    """
    Get a specific customer by ID.

    Requires admin authentication.
    """
    doc = db.collection("customers").document(customer_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    customer_data = doc.to_dict()
    customer_data["customer_id"] = doc.id
    customer_data["created_at"] = customer_data.get("created_at", datetime.now())

    return CustomerResponse(**customer_data)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    update_data: UpdateCustomerRequest,
    db: DB,
    admin: Admin,
):
    """
    Update customer information.

    Requires admin authentication.
    """
    doc = db.collection("customers").document(customer_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Build update dict (only include non-None fields)
    update_dict = {}
    if update_data.name is not None:
        update_dict["name"] = update_data.name
    if update_data.whatsapp is not None:
        update_dict["whatsapp"] = update_data.whatsapp
    if update_data.address is not None:
        update_dict["address"] = update_data.address
    if update_data.customer_level is not None:
        update_dict["customer_level"] = update_data.customer_level

    update_dict["updated_at"] = SERVER_TIMESTAMP

    # Update customer
    db.collection("customers").document(customer_id).update(update_dict)

    # Get updated customer
    updated_doc = db.collection("customers").document(customer_id).get()
    customer_data = updated_doc.to_dict()
    customer_data["customer_id"] = customer_id
    customer_data["created_at"] = customer_data.get("created_at", datetime.now())

    return CustomerResponse(**customer_data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str, db: DB, admin: Admin):
    """
    Delete a customer record.

    ⚠️ CAUTION: This operation cannot be undone.

    Requires admin authentication.
    """
    doc = db.collection("customers").document(customer_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Delete customer
    db.collection("customers").document(customer_id).delete()

    return None
