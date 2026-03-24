"""
Xero API wrapper functions with automatic token refresh.

Provides wrapper functions for Xero API calls that automatically handle
token expiry and refresh.
"""
import requests
import json
from typing import Optional, Dict, Any, Union
from utils.xero_token_manager import XeroTokenManager

# Global token manager instance (set by init_wrapper)
_token_manager: Optional[XeroTokenManager] = None

def init_wrapper(token_manager: XeroTokenManager) -> None:
    """
    Initialize the wrapper with a token manager instance.

    Args:
        token_manager: Initialized XeroTokenManager instance
    """
    global _token_manager
    _token_manager = token_manager

def make_xero_request(
    url: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    tenant_id: str = "",
    headers: Optional[Dict] = None,
    refresh_threshold: int = 300
) -> requests.Response:
    """
    Make a Xero API request with automatic token refresh.

    Args:
        url: Xero API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        json_data: JSON data for POST/PUT requests
        tenant_id: Xero organization tenant ID (required)
        headers: Additional headers to include (Authorization and xero-tenant-id will be added)
        refresh_threshold: Refresh token if expires within this many seconds (default 5 minutes)

    Returns:
        requests.Response object

    Raises:
        ValueError: If token manager not initialized or tenant_id not provided
        RuntimeError: If unable to get valid token after refresh attempt
    """
    if _token_manager is None:
        raise ValueError("Token manager not initialized. Call init_wrapper() first.")

    if not tenant_id:
        raise ValueError("tenant_id is required for Xero API requests")

    # Get valid access token
    access_token = _token_manager.get_valid_token(tenant_id, refresh_threshold)
    if not access_token:
        raise RuntimeError(f"Unable to get valid access token for tenant {tenant_id}")

    # Prepare headers
    request_headers = {
        "Authorization": f"Bearer {access_token}",
        "xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    if headers:
        request_headers.update(headers)

    # Make the request
    method = method.upper()
    try:
        if method == "GET":
            response = requests.get(url, headers=request_headers)
        elif method == "POST":
            response = requests.post(url, headers=request_headers, json=json_data)
        elif method == "PUT":
            response = requests.put(url, headers=request_headers, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url, headers=request_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Handle 401 Unauthorized (token may have expired between check and request)
        if response.status_code == 401:
            print("Received 401 Unauthorized. Attempting token refresh and retry...")
            # Try to refresh token
            new_tokens = _token_manager.refresh_access_token(tenant_id)
            if new_tokens:
                # Update access token and retry
                request_headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                # Retry the request
                if method == "GET":
                    response = requests.get(url, headers=request_headers)
                elif method == "POST":
                    response = requests.post(url, headers=request_headers, json=json_data)
                elif method == "PUT":
                    response = requests.put(url, headers=request_headers, json=json_data)
                elif method == "DELETE":
                    response = requests.delete(url, headers=request_headers)
            else:
                print("Token refresh failed after 401 response")

        return response

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise

def create_xero_invoice(invoice_data: Dict, tenant_id: str) -> requests.Response:
    """
    Create a Xero invoice with automatic token handling.

    Args:
        invoice_data: Invoice data in Xero format
        tenant_id: Xero organization tenant ID

    Returns:
        requests.Response object
    """
    url = "https://api.xero.com/api.xro/2.0/Invoices"
    return make_xero_request(url, "POST", invoice_data, tenant_id)

def create_xero_quote(quote_data: Dict, tenant_id: str) -> requests.Response:
    """
    Create a Xero quote with automatic token handling.

    Args:
        quote_data: Quote data in Xero format
        tenant_id: Xero organization tenant ID

    Returns:
        requests.Response object
    """
    url = "https://api.xero.com/api.xro/2.0/Quotes"
    return make_xero_request(url, "POST", quote_data, tenant_id)

def get_xero_invoices(tenant_id: str, params: Optional[Dict] = None) -> requests.Response:
    """
    Get invoices from Xero with automatic token handling.

    Args:
        tenant_id: Xero organization tenant ID
        params: Query parameters (e.g., status, page)

    Returns:
        requests.Response object
    """
    url = "https://api.xero.com/api.xro/2.0/Invoices"
    # Build query string if params provided
    if params:
        from urllib.parse import urlencode
        query_string = urlencode(params)
        url = f"{url}?{query_string}"

    return make_xero_request(url, "GET", tenant_id=tenant_id)

def get_xero_quotes(tenant_id: str, params: Optional[Dict] = None) -> requests.Response:
    """
    Get quotes from Xero with automatic token handling.

    Args:
        tenant_id: Xero organization tenant ID
        params: Query parameters

    Returns:
        requests.Response object
    """
    url = "https://api.xero.com/api.xro/2.0/Quotes"
    if params:
        from urllib.parse import urlencode
        query_string = urlencode(params)
        url = f"{url}?{query_string}"

    return make_xero_request(url, "GET", tenant_id=tenant_id)

# Convenience function for Flask apps
def setup_flask_wrapper(app, config):
    """
    Convenience function to setup token manager for Flask apps.

    Args:
        app: Flask application instance
        config: Config object with Xero credentials (client_id, client_secret, redirect_uri)
    """
    token_manager = XeroTokenManager(
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=config.redirect_uri
    )
    init_wrapper(token_manager)
    return token_manager