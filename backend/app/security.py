from fastapi import Header, HTTPException

def require_user_id(x_user_id: str = Header(None, alias="X-User-Id")) -> str:
    """
    Require X-User-Id header for all protected endpoints.
    In production, integrate with your auth provider (Clerk, Auth0, etc.)
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="X-User-Id header required. Please authenticate."
        )
    return x_user_id
