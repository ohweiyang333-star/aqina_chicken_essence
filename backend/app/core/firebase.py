"""Firebase Admin SDK initialization."""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.exceptions import FirebaseError
from app.core.config import settings

# Global Firebase app instances
_firestore_db: firestore.Client | None = None
_firebase_auth: auth.Client | None = None


def get_firebase_app() -> firebase_admin.App:
    """Get or initialize Firebase app."""
    if not firebase_admin._apps:
        # Initialize with default credentials (from environment variable or service account)
        # In production, use GOOGLE_APPLICATION_CREDENTIALS environment variable
        # Or use application default credentials
        try:
            # Try using service account from environment variable
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    "projectId": settings.firebase_project_id,
                    "storageBucket": settings.firebase_storage_bucket,
                })
            else:
                # Use application default credentials (works in Cloud Run)
                firebase_admin.initialize_app(options={
                    "projectId": settings.firebase_project_id,
                    "storageBucket": settings.firebase_storage_bucket,
                })
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            raise

    return firebase_admin.get_app()


def get_firestore() -> firestore.Client:
    """Get Firestore client."""
    global _firestore_db
    if _firestore_db is None:
        app = get_firebase_app()
        _firestore_db = firestore.client(app)
    return _firestore_db


def get_firebase_auth() -> auth.Client:
    """Get Firebase Auth client."""
    global _firebase_auth
    if _firebase_auth is None:
        app = get_firebase_app()
        _firebase_auth = auth.Client(app)
    return _firebase_auth


# Export convenience functions
db = get_firestore
firebase_auth = get_firebase_auth
