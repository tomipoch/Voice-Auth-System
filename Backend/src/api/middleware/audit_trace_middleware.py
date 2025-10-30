"""Audit trace middleware for request/response logging."""

import time
import uuid
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class AuditTraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit trail and request tracing.
    Logs all API requests and responses for compliance and debugging.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_headers = {
            "authorization", "x-api-key", "cookie", "set-cookie"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with audit logging."""
        
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract client info
        client_id = getattr(request.state, "client_id", "unknown")
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        start_time = time.time()
        
        self._log_request(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_id=client_id,
            client_ip=client_ip,
            user_agent=user_agent,
            headers=self._sanitize_headers(dict(request.headers)),
            query_params=dict(request.query_params)
        )
        
        # Process request
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Log successful response
            self._log_response(
                request_id=request_id,
                status_code=response.status_code,
                processing_time=processing_time,
                headers=self._sanitize_headers(dict(response.headers)),
                success=True
            )
            
            # Add trace headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log error response
            self._log_response(
                request_id=request_id,
                status_code=500,
                processing_time=processing_time,
                error_message=str(e),
                success=False
            )
            
            # Re-raise the exception
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers first (when behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive information from headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _log_request(
        self,
        request_id: str,
        method: str,
        url: str,
        client_id: str,
        client_ip: str,
        user_agent: str,
        headers: dict,
        query_params: dict
    ):
        """Log incoming request details."""
        log_data = {
            "event_type": "api_request",
            "request_id": request_id,
            "timestamp": time.time(),
            "method": method,
            "url": url,
            "client_id": client_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": headers,
            "query_params": query_params
        }
        
        logger.info(f"API Request: {json.dumps(log_data)}")
    
    def _log_response(
        self,
        request_id: str,
        status_code: int,
        processing_time: float,
        headers: dict = None,
        error_message: str = None,
        success: bool = True
    ):
        """Log response details."""
        log_data = {
            "event_type": "api_response",
            "request_id": request_id,
            "timestamp": time.time(),
            "status_code": status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "success": success
        }
        
        if headers:
            log_data["headers"] = headers
        
        if error_message:
            log_data["error_message"] = error_message
        
        if success:
            logger.info(f"API Response: {json.dumps(log_data)}")
        else:
            logger.error(f"API Error: {json.dumps(log_data)}")
    
    def _log_audit_event(
        self,
        request_id: str,
        actor: str,
        action: str,
        resource: str,
        success: bool = True,
        metadata: dict = None
    ):
        """Log specific audit events."""
        audit_data = {
            "event_type": "audit_event",
            "request_id": request_id,
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "success": success,
            "metadata": metadata or {}
        }
        
        logger.info(f"Audit Event: {json.dumps(audit_data)}")