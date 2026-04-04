"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleLoginRequest(BaseModel):
    """Request model for Google login."""

    id_token: str = Field(..., description="Google ID token from Firebase Auth")


class GoogleLoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: Optional[str] = Field(None, description="Session access token (optional)")
    is_admin: bool = Field(..., description="Whether the user is an admin")
    user_id: str = Field(..., description="Firebase Auth UID")
    email: str = Field(..., description="User email")


@router.post("/google-login", response_model=GoogleLoginResponse)
async def google_login(request: GoogleLoginRequest):
    """
    Authenticate user with Google ID token.

    Verifies the Firebase ID token and checks if the user is an admin
    by looking up their UID in the admin_users collection.
    """
    from app.core.security import verify_google_id_token
    from app.core.firebase import get_firestore

    try:
        # Verify the ID token
        decoded_token = await verify_google_id_token(request.id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        if not uid or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Check if user is an admin
        db = get_firestore()
        admin_doc = db.collection("admin_users").document(uid).get()
        is_admin = admin_doc.exists

        # In a production app, you would generate a JWT session token here
        # For now, we return the Firebase ID token as the access token
        return GoogleLoginResponse(
            access_token=request.id_token,  # In production, generate new JWT
            is_admin=is_admin,
            user_id=uid,
            email=email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
