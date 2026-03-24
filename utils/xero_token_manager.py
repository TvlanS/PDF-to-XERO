"""
Xero Token Manager for handling OAuth 2.0 token lifecycle.
Provides methods for initial authentication, token refresh, and validation.
"""
import requests
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from utils.token_storage import save_tokens, load_tokens, delete_tokens, is_token_expired

class XeroTokenManager:
    """
    Manages Xero OAuth 2.0 tokens including refresh logic.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,
                 token_url: str = "https://identity.xero.com/connect/token",
                 auth_url: str = "https://login.xero.com/identity/connect/authorize"):
        """
        Initialize token manager with Xero app credentials.

        Args:
            client_id: Xero OAuth client ID
            client_secret: Xero OAuth client secret
            redirect_uri: Redirect URI registered in Xero app
            token_url: Xero token endpoint URL
            auth_url: Xero authorization endpoint URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.auth_url = auth_url

        # Prepare Basic Auth header for token requests
        credentials = f"{self.client_id}:{self.client_secret}"
        self.b64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def handle_initial_auth(self, auth_code: str, scope: str = "offline_access accounting.transactions") -> Tuple[Optional[dict], Optional[str]]:
        """
        Exchange authorization code for initial tokens and save them.

        Args:
            auth_code: Authorization code from Xero callback
            scope: OAuth scope (default includes offline_access for refresh tokens)

        Returns:
            Tuple of (token_response, tenant_id) or (None, None) on error
        """
        try:
            # Exchange code for tokens
            token_response = self._exchange_auth_code(auth_code)

            if "access_token" not in token_response or "refresh_token" not in token_response:
                print("Error: Token response missing access_token or refresh_token")
                return None, None

            # Get tenant ID using the new access token
            access_token = token_response["access_token"]
            tenant_id = self._get_tenant_id(access_token)

            if not tenant_id:
                print("Error: Could not retrieve tenant ID")
                return None, None

            # Save tokens to storage
            save_tokens(tenant_id, token_response)

            return token_response, tenant_id

        except Exception as e:
            print(f"Error during initial authentication: {e}")
            return None, None

    def refresh_access_token(self, tenant_id: str) -> Optional[dict]:
        """
        Refresh access token using refresh token.

        Args:
            tenant_id: Xero organization tenant ID

        Returns:
            New token response dict, or None on error
        """
        # Load existing tokens
        token_data = load_tokens(tenant_id)
        if not token_data or "refresh_token" not in token_data:
            print(f"No refresh token found for tenant {tenant_id}")
            return None

        refresh_token = token_data["refresh_token"]

        try:
            # Request new tokens using refresh token
            response = requests.post(
                self.token_url,
                headers={
                    "Authorization": f"Basic {self.b64_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )

            if response.status_code != 200:
                print(f"Token refresh failed: {response.status_code} {response.text}")
                return None

            new_tokens = response.json()

            # Xero may not return a new refresh token in some cases
            # If not provided, keep the old refresh token
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token

            # Save updated tokens
            save_tokens(tenant_id, new_tokens)
            print(f"Tokens refreshed for tenant {tenant_id}")

            return new_tokens

        except Exception as e:
            print(f"Error refreshing access token: {e}")
            return None

    def get_valid_token(self, tenant_id: str, refresh_threshold: int = 300) -> Optional[str]:
        """
        Get a valid access token for a tenant, refreshing if necessary.

        Args:
            tenant_id: Xero organization tenant ID
            refresh_threshold: Refresh if token expires within this many seconds (default 5 minutes)

        Returns:
            Valid access token string, or None if unable to get valid token
        """
        # Load tokens from storage
        token_data = load_tokens(tenant_id)

        # If no tokens stored, need to re-authenticate
        if not token_data:
            print(f"No tokens found for tenant {tenant_id}. Re-authentication required.")
            return None

        # Check if token needs refresh
        if is_token_expired(token_data, refresh_threshold):
            print(f"Token for tenant {tenant_id} expired or near expiry. Refreshing...")
            new_tokens = self.refresh_access_token(tenant_id)

            if new_tokens:
                # Return new access token
                return new_tokens.get("access_token")
            else:
                # Refresh failed, tokens may be invalid
                print(f"Token refresh failed for tenant {tenant_id}. Re-authentication required.")
                # Optionally delete invalid tokens
                delete_tokens(tenant_id)
                return None
        else:
            # Token still valid
            return token_data.get("access_token")

    def _exchange_auth_code(self, auth_code: str) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            auth_code: Authorization code from Xero callback

        Returns:
            Token response dict from Xero
        """
        response = requests.post(
            self.token_url,
            headers={
                "Authorization": f"Basic {self.b64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.redirect_uri
            }
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.status_code} {response.text}")

        return response.json()

    def _get_tenant_id(self, access_token: str) -> Optional[str]:
        """
        Get tenant ID from Xero connections endpoint.

        Args:
            access_token: Valid access token

        Returns:
            Tenant ID string, or None on error
        """
        try:
            response = requests.get(
                "https://api.xero.com/connections",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                print(f"Failed to get connections: {response.status_code} {response.text}")
                return None

            connections = response.json()
            if not connections:
                print("No connections/tenants found")
                return None

            # Return first tenant ID (most users have one organization)
            return connections[0]["tenantId"]

        except Exception as e:
            print(f"Error getting tenant ID: {e}")
            return None

    def get_auth_url(self, scope: str = "offline_access accounting.transactions") -> str:
        """
        Generate authorization URL for initial OAuth flow.

        Args:
            scope: OAuth scope string

        Returns:
            Authorization URL to redirect user to
        """
        scope = scope.replace(" ", "%20")
        return f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}"