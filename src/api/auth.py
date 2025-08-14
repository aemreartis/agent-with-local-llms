"""
Authentication Middleware - Stage 7 TDD Implementation

JWT-based authentication and authorization middleware.
Following TDD methodology: Auth logic defined first, then integration.
"""

import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import uuid
import os
from functools import wraps

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security scheme
security = HTTPBearer()


class AuthService:
    """Authentication service for JWT token management"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh an access token using a refresh token"""
        payload = self.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        user_data = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "permissions": payload.get("permissions", [])
        }
        return self.create_access_token(user_data)


class UserManager:
    """User management service (mock implementation for testing)"""
    
    def __init__(self):
        # Mock user database - in production, this would be a real database
        self.users = {
            "admin": {
                "user_id": "admin_001",
                "username": "admin",
                "hashed_password": pwd_context.hash("admin123"),
                "permissions": ["read", "write", "admin"],
                "is_active": True
            },
            "user": {
                "user_id": "user_001",
                "username": "user",
                "hashed_password": pwd_context.hash("user123"),
                "permissions": ["read", "write"],
                "is_active": True
            },
            "readonly": {
                "user_id": "readonly_001",
                "username": "readonly",
                "hashed_password": pwd_context.hash("readonly123"),
                "permissions": ["read"],
                "is_active": True
            }
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        user = self.users.get(username)
        if not user:
            return None
        
        if not pwd_context.verify(password, user["hashed_password"]):
            return None
        
        if not user["is_active"]:
            return None
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        for user in self.users.values():
            if user["user_id"] == user_id:
                return user
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.users.get(username)


# Global instances
auth_service = AuthService()
user_manager = UserManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict[str, Any] = Depends(get_current_active_user), **kwargs):
            user_permissions = current_user.get("permissions", [])
            
            # Check if user has all required permissions
            for permission in required_permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {permission}"
                    )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """Decorator to require admin permissions"""
    return require_permissions(["admin"])(func)


def require_write_permission(func):
    """Decorator to require write permissions"""
    return require_permissions(["write"])(func)


def require_read_permission(func):
    """Decorator to require read permissions"""
    return require_permissions(["read"])(func)


# Mock authentication for testing
class MockAuthService:
    """Mock authentication service for testing"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY  # Use the same secret key as AuthService
        self.algorithm = "HS256"
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a mock access token"""
        to_encode = data.copy()
        to_encode.update({"exp": datetime.now(UTC) + timedelta(hours=1), "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a mock token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


# Rate limiting
class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
    
    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False


rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request=None, **kwargs):
            if request:
                client_ip = request.client.host
                if not rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator 