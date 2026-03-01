"""Authentication middleware for API key validation and rate limiting."""

import time
import hashlib
import os
import json
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Constants
JSON_CONTENT_TYPE = "application/json"


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication and rate limiting.
    Implements the Middleware Pattern for cross-cutting concerns.
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Load API keys from environment variable (JSON format)
        # Example: API_KEYS='{"my-api-key": {"client_id": "client-1", "client_name": "My Client", "rate_limit": 100, "permissions": ["verify", "enroll"]}}'
        api_keys_json = os.getenv("API_KEYS", "{}")
        try:
            self._valid_api_keys = json.loads(api_keys_json)
        except json.JSONDecodeError:
            logger.error("Invalid API_KEYS format. Expected JSON object.")
            self._valid_api_keys = {}
        
        # In development, add demo keys if none configured
        if not self._valid_api_keys and os.getenv("ENV", "development") != "production":
            logger.warning("⚠️  No API_KEYS configured. Using demo keys for development.")
            self._valid_api_keys = {
                "dev-api-key": {
                    "client_id": "dev-client",
                    "client_name": "Development Client",
                    "rate_limit": 1000,
                    "permissions": ["verify", "enroll", "challenge"]
                }
            }
        
        # Rate limiting tracking
        # WARNING: In-memory store is NOT suitable for distributed systems
        if os.getenv("ENV") == "production":
            logger.warning("⚠️  Using in-memory rate limiting. Use Redis for production!")
        self._rate_limit_store: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication and rate limiting."""
        
        # Skip auth for health check, docs, auth endpoints, and development mode
        skip_paths = ["/health", "/docs", "/openapi.json", "/api/auth/login", "/api/auth/register"]
        
        skip_auth = os.getenv('SKIP_AUTH', 'false').lower() == 'true'
        development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
        
        if request.url.path in skip_paths or skip_auth or development_mode:
            if development_mode:
                request.state.client_id = "dev-client"
                request.state.client_name = "Development Client"
            return await call_next(request)
        
        # Extract API key (headers only - no query params for security)
        api_key = self._extract_api_key(request)
        
        if not api_key:
            return self._unauthorized_response("Missing API key")
        
        # Validate API key
        client_info = self._validate_api_key(api_key)
        if not client_info:
            return self._unauthorized_response("Invalid API key")
        
        # Check rate limits
        if not self._check_rate_limit(client_info["client_id"], client_info["rate_limit"]):
            return self._rate_limit_response()
        
        # Check permissions
        endpoint_permission = self._get_endpoint_permission(request.url.path)
        if endpoint_permission and endpoint_permission not in client_info["permissions"]:
            return self._forbidden_response(f"Permission '{endpoint_permission}' required")
        
        # Add client info to request state
        request.state.client_id = client_info["client_id"]
        request.state.client_name = client_info["client_name"]
        request.state.api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Add response headers
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
        response.headers["X-Client-ID"] = client_info["client_id"]
        response.headers["X-Rate-Limit-Remaining"] = str(
            self._get_remaining_requests(client_info["client_id"], client_info["rate_limit"])
        )
        
        return response
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers only (no query params for security)."""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Try X-API-Key header
        return request.headers.get("X-API-Key")
    
    def _validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return client info."""
        return self._valid_api_keys.get(api_key)
    
    def _check_rate_limit(self, client_id: str, rate_limit: int) -> bool:
        """Check if client is within rate limits."""
        current_time = time.time()
        current_hour = int(current_time // 3600)
        
        if client_id not in self._rate_limit_store:
            self._rate_limit_store[client_id] = {}
        
        client_store = self._rate_limit_store[client_id]
        
        # Clean old entries
        old_keys = [k for k in client_store.keys() if k < current_hour - 1]
        for key in old_keys:
            del client_store[key]
        
        # Check current hour
        current_count = client_store.get(current_hour, 0)
        if current_count >= rate_limit:
            return False
        
        # Increment counter
        client_store[current_hour] = current_count + 1
        return True
    
    def _get_remaining_requests(self, client_id: str, rate_limit: int) -> int:
        """Get remaining requests for the current hour."""
        current_hour = int(time.time() // 3600)
        current_count = self._rate_limit_store.get(client_id, {}).get(current_hour, 0)
        return max(0, rate_limit - current_count)
    
    def _get_endpoint_permission(self, path: str) -> Optional[str]:
        """Map endpoint path to required permission."""
        if "/enrollment" in path:
            return "enroll"
        elif "/verification" in path or "/verify" in path:
            return "verify"
        elif "/challenge" in path:
            return "challenge"
        return None
    
    def _unauthorized_response(self, message: str) -> Response:
        """Return 401 Unauthorized response."""
        return Response(
            content=f'{{"error": "Unauthorized", "message": "{message}"}}',
            status_code=401,
            headers={"Content-Type": JSON_CONTENT_TYPE}
        )
    
    def _forbidden_response(self, message: str) -> Response:
        """Return 403 Forbidden response."""
        return Response(
            content=f'{{"error": "Forbidden", "message": "{message}"}}',
            status_code=403,
            headers={"Content-Type": JSON_CONTENT_TYPE}
        )
    
    def _rate_limit_response(self) -> Response:
        """Return 429 Too Many Requests response."""
        return Response(
            content='{"error": "Rate limit exceeded", "message": "Too many requests"}',
            status_code=429,
            headers={"Content-Type": JSON_CONTENT_TYPE}
        )