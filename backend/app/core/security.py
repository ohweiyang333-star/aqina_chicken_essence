"""Security utilities for authentication and authorization."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
from app.core.firebase import get_firestore
from app.core.config import settings

# Security scheme for Bearer tokens
security = HTTPBearer(auto_error=False)


async def verify_google_id_token(id_token: str) -> dict:
    """
    Verify Google ID Token from Firebase Auth.

    Args:
        id_token: The Firebase ID token to verify

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID token has expired"
        )
    except InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """
    Verify the user is an admin by checking the admin_users collection.

    Args:
        credentials: HTTP Bearer credentials from the request

    Returns:
        Admin user data including uid, email

    Raises:
        HTTPException: If not authenticated or not an admin
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify the ID token
    decoded_token = await verify_google_id_token(credentials.credentials)
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Check if user is in admin_users collection
    db = get_firestore()
    admin_doc = db.collection("admin_users").document(uid).get()

    if not admin_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as admin"
        )

    # Return admin user data
    admin_data = admin_doc.to_dict()
    admin_data["uid"] = uid
    admin_data["email"] = email

    return admin_data


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """
    Get the current authenticated user (without admin check).

    Args:
        credentials: HTTP Bearer credentials from the request

    Returns:
        User data from decoded token

    Raises:
        HTTPException: If not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    decoded_token = await verify_google_id_token(credentials.credentials)
    return decoded_token


# Type aliases for dependency injection
AdminUser = Annotated[dict, Depends(get_current_admin)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalCurrentUser = Annotated[dict | None, Depends(get_current_user)]
