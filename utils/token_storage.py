"""
Token storage utilities for Xero OAuth 2.0 tokens.
Handles reading/writing tokens to JSON files in config/tokens/ directory.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

def get_token_storage_path() -> Path:
    """Get the path to the token storage directory."""
    # Base directory is the project root
    base_dir = Path(__file__).parent
    # Default to config/tokens/ relative to project root
    token_dir = base_dir / "config" / "tokens"
    token_dir.mkdir(parents=True, exist_ok=True)
    return token_dir

def get_token_file_path(tenant_id: str) -> Path:
    """Get the file path for a tenant's tokens."""
    token_dir = get_token_storage_path()
    # Sanitize tenant_id for filename (replace any non-alphanumeric with underscore)
    safe_tenant_id = "".join(c if c.isalnum() else "_" for c in tenant_id)
    return token_dir / f"{safe_tenant_id}_tokens.json"

def save_tokens(tenant_id: str, token_response: dict) -> None:
    """
    Save tokens from Xero token response to a JSON file.

    Args:
        tenant_id: Xero organization tenant ID
        token_response: Dictionary from Xero token endpoint containing:
            - access_token
            - refresh_token
            - expires_in (seconds until expiry)
            - scope (optional)
    """
    # Calculate expiry timestamp
    expires_in = token_response.get("expires_in", 1800)  # Default 30 minutes
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # Prepare token data for storage
    token_data = {
        "tenant_id": tenant_id,
        "access_token": token_response.get("access_token"),
        "refresh_token": token_response.get("refresh_token"),
        "expires_at": expires_at.isoformat() + "Z",  # ISO format with Z for UTC
        "scope": token_response.get("scope", ""),
        "last_refreshed": datetime.utcnow().isoformat() + "Z"
    }

    # Write to file
    token_file = get_token_file_path(tenant_id)
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"Tokens saved for tenant {tenant_id} at {token_file}")

def load_tokens(tenant_id: str) -> dict:
    """
    Load tokens from storage for a tenant.

    Args:
        tenant_id: Xero organization tenant ID

    Returns:
        Dictionary with token data, or empty dict if not found
    """
    token_file = get_token_file_path(tenant_id)
    if not token_file.exists():
        return {}

    try:
        with open(token_file, "r") as f:
            token_data = json.load(f)

        # Validate required fields
        required = ["access_token", "refresh_token", "expires_at"]
        if not all(field in token_data for field in required):
            print(f"Token file {token_file} missing required fields")
            return {}

        return token_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading tokens from {token_file}: {e}")
        return {}

def delete_tokens(tenant_id: str) -> bool:
    """
    Delete token file for a tenant.

    Args:
        tenant_id: Xero organization tenant ID

    Returns:
        True if deleted, False if file didn't exist or error
    """
    token_file = get_token_file_path(tenant_id)
    if token_file.exists():
        try:
            token_file.unlink()
            print(f"Deleted token file for tenant {tenant_id}")
            return True
        except OSError as e:
            print(f"Error deleting token file {token_file}: {e}")
            return False
    return False

def is_token_expired(token_data: dict, refresh_threshold: int = 300) -> bool:
    """
    Check if token is expired or near expiry.

    Args:
        token_data: Dictionary with "expires_at" (ISO format string)
        refresh_threshold: Refresh if token expires within this many seconds (default 5 minutes)

    Returns:
        True if token should be refreshed, False if still valid
    """
    expires_at_str = token_data.get("expires_at")
    if not expires_at_str:
        return True  # No expiry time means token is invalid

    try:
        # Parse ISO format string (handles both with and without Z)
        if expires_at_str.endswith("Z"):
            expires_at = datetime.fromisoformat(expires_at_str[:-1])
        else:
            expires_at = datetime.fromisoformat(expires_at_str)

        # Calculate time remaining
        time_remaining = expires_at - datetime.utcnow()

        # Return True if token expires within refresh_threshold seconds
        return time_remaining.total_seconds() <= refresh_threshold
    except (ValueError, TypeError) as e:
        print(f"Error parsing expiry time {expires_at_str}: {e}")
        return True

def get_all_tenant_ids() -> list:
    """
    Get list of all tenant IDs with stored tokens.

    Returns:
        List of tenant IDs (unsanitized from token files)
    """
    token_dir = get_token_storage_path()
    tenant_ids = []

    for token_file in token_dir.glob("*_tokens.json"):
        try:
            with open(token_file, "r") as f:
                token_data = json.load(f)
                if "tenant_id" in token_data:
                    tenant_ids.append(token_data["tenant_id"])
        except (json.JSONDecodeError, IOError):
            continue

    return tenant_ids