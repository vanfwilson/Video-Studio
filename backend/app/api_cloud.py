"""
Cloud Connections API - Manages YouTube channels, Dropbox, Google Drive, OneDrive connections.

n8n handles the actual OAuth credentials. This API just stores which accounts/folders
the user has connected and selected for use.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db import SessionLocal
from app.security import require_user_id
from app.models import CloudConnection, User

router = APIRouter(prefix="/cloud", tags=["cloud"])

SUPPORTED_PROVIDERS = ["youtube", "dropbox", "gdrive", "onedrive"]

def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_user(db: Session, user_id: str):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        db.add(User(id=user_id))
        db.commit()

def serialize_connection(c: CloudConnection) -> dict:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "provider": c.provider,
        "account_id": c.account_id,
        "account_name": c.account_name,
        "account_email": c.account_email,
        "profile_photo_url": c.profile_photo_url,
        "selected_folder_path": c.selected_folder_path,
        "selected_folder_name": c.selected_folder_name,
        "is_active": c.is_active == "true",
        "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
        "metadata": c.extra_data,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

@router.get("")
def list_connections(
    provider: Optional[str] = None,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """List all cloud connections for the user, optionally filtered by provider."""
    ensure_user(db, user_id)
    query = db.query(CloudConnection).filter(CloudConnection.user_id == user_id)
    if provider:
        query = query.filter(CloudConnection.provider == provider)
    rows = query.order_by(CloudConnection.id.desc()).all()
    return [serialize_connection(c) for c in rows]

@router.get("/{connection_id}")
def get_connection(
    connection_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """Get a specific cloud connection."""
    c = db.query(CloudConnection).filter(
        CloudConnection.id == connection_id,
        CloudConnection.user_id == user_id
    ).first()
    if not c:
        raise HTTPException(404, "Connection not found")
    return serialize_connection(c)

@router.post("")
def create_connection(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """
    Create/register a cloud connection.

    For YouTube: store channel_id in account_id, channel name in account_name
    For cloud storage: store folder path/id as selected_folder_path

    Payload:
    {
        "provider": "youtube" | "dropbox" | "gdrive" | "onedrive",
        "account_id": "channel_id or account identifier",
        "account_name": "display name",
        "account_email": "optional email",
        "profile_photo_url": "optional photo",
        "selected_folder_path": "for cloud storage - path or folder id",
        "selected_folder_name": "for cloud storage - folder display name",
        "metadata": { ... any extra data ... }
    }
    """
    ensure_user(db, user_id)

    provider = payload.get("provider", "").lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(400, f"Provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}")

    # Check if connection already exists for this provider+account
    existing = db.query(CloudConnection).filter(
        CloudConnection.user_id == user_id,
        CloudConnection.provider == provider,
        CloudConnection.account_id == payload.get("account_id")
    ).first()

    if existing:
        # Update existing connection
        existing.account_name = payload.get("account_name") or existing.account_name
        existing.account_email = payload.get("account_email") or existing.account_email
        existing.profile_photo_url = payload.get("profile_photo_url") or existing.profile_photo_url
        existing.selected_folder_path = payload.get("selected_folder_path") or existing.selected_folder_path
        existing.selected_folder_name = payload.get("selected_folder_name") or existing.selected_folder_name
        existing.is_active = "true"
        existing.extra_data = payload.get("metadata") or existing.extra_data
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return serialize_connection(existing)

    # Create new connection
    conn = CloudConnection(
        user_id=user_id,
        provider=provider,
        account_id=payload.get("account_id"),
        account_name=payload.get("account_name"),
        account_email=payload.get("account_email"),
        profile_photo_url=payload.get("profile_photo_url"),
        selected_folder_path=payload.get("selected_folder_path"),
        selected_folder_name=payload.get("selected_folder_name"),
        is_active="true",
        extra_data=payload.get("metadata"),
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return serialize_connection(conn)

@router.patch("/{connection_id}")
def update_connection(
    connection_id: int,
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """Update a cloud connection (e.g., change selected folder)."""
    c = db.query(CloudConnection).filter(
        CloudConnection.id == connection_id,
        CloudConnection.user_id == user_id
    ).first()
    if not c:
        raise HTTPException(404, "Connection not found")

    allowed = {
        "account_name", "account_email", "profile_photo_url",
        "selected_folder_path", "selected_folder_name", "is_active", "metadata"
    }
    for k, v in payload.items():
        if k in allowed:
            if k == "is_active":
                c.is_active = "true" if v else "false"
            elif k == "metadata":
                c.extra_data = v
            else:
                setattr(c, k, v)

    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return serialize_connection(c)

@router.delete("/{connection_id}")
def delete_connection(
    connection_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """Delete/disconnect a cloud connection."""
    c = db.query(CloudConnection).filter(
        CloudConnection.id == connection_id,
        CloudConnection.user_id == user_id
    ).first()
    if not c:
        raise HTTPException(404, "Connection not found")

    db.delete(c)
    db.commit()
    return {"ok": True, "deleted_id": connection_id}

@router.get("/status/{provider}")
def get_provider_status(
    provider: str,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """Check if user has an active connection for a provider."""
    provider = provider.lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(400, f"Provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}")

    conn = db.query(CloudConnection).filter(
        CloudConnection.user_id == user_id,
        CloudConnection.provider == provider,
        CloudConnection.is_active == "true"
    ).first()

    return {
        "connected": conn is not None,
        "connection": serialize_connection(conn) if conn else None
    }
