"""
Authentication integration with Supabase
"""

import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request

from .config import settings
from .database import supabase_client

logger = structlog.get_logger()

security = HTTPBearer()


class SupabaseAuth:
    """Supabase authentication utilities"""
    
    def __init__(self):
        self.supabase = supabase_client
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Supabase JWT token"""
        try:
            # Verify token with Supabase
            user = self.supabase.client.auth.get_user(token)
            
            if user and user.user:
                user_data = {
                    'id': user.user.id,
                    'email': user.user.email,
                    'role': user.user.role if hasattr(user.user, 'role') else 'authenticated',
                    'metadata': user.user.user_metadata or {},
                    'app_metadata': user.user.app_metadata or {},
                    'created_at': user.user.created_at,
                    'updated_at': user.user.updated_at
                }
                
                logger.info("Token verified successfully", user_id=user_data['id'])
                return user_data
            
            logger.warning("Invalid token - no user found")
            return None
            
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by ID"""
        try:
            # This would typically use the admin client
            # For now, we'll return basic user info
            user_data = {
                'id': user_id,
                'email': f"user_{user_id}@example.com",  # Placeholder
                'role': 'authenticated'
            }
            
            return user_data
            
        except Exception as e:
            logger.error("Failed to get user by ID", error=str(e), user_id=user_id)
            return None
    
    async def create_user_session(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create user session (sign in)"""
        try:
            response = self.supabase.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                session_data = {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'expires_at': response.session.expires_at,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'role': response.user.role if hasattr(response.user, 'role') else 'authenticated'
                    }
                }
                
                logger.info("User session created", user_id=response.user.id)
                return session_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to create user session", error=str(e))
            return None
    
    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh user session"""
        try:
            response = self.supabase.client.auth.refresh_session(refresh_token)
            
            if response.session:
                session_data = {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'expires_at': response.session.expires_at
                }
                
                logger.info("Session refreshed successfully")
                return session_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to refresh session", error=str(e))
            return None
    
    async def sign_out(self, token: str) -> bool:
        """Sign out user"""
        try:
            self.supabase.client.auth.sign_out()
            logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to sign out user", error=str(e))
            return False


class AuthenticationManager:
    """Authentication manager for API endpoints"""
    
    def __init__(self):
        self.supabase_auth = SupabaseAuth()
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Get current authenticated user"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticação necessário",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = await self.supabase_auth.verify_token(credentials.credentials)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticação inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data
    
    async def get_optional_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get current user if authenticated, None otherwise"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            return await self.supabase_auth.verify_token(token)
            
        except Exception:
            return None
    
    def require_role(self, required_roles: List[str]):
        """Decorator to require specific roles"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Get user from kwargs (should be injected by dependency)
                user = kwargs.get('current_user')
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Autenticação necessária"
                    )
                
                user_role = user.get('role', 'authenticated')
                if user_role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Permissões insuficientes"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class RoleBasedAccess:
    """Role-based access control"""
    
    ROLES = {
        'admin': ['read', 'write', 'delete', 'manage_users'],
        'manager': ['read', 'write', 'delete'],
        'user': ['read', 'write'],
        'viewer': ['read'],
        'authenticated': ['read']  # Default role
    }
    
    @classmethod
    def has_permission(cls, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        role_permissions = cls.ROLES.get(user_role, [])
        return required_permission in role_permissions
    
    @classmethod
    def can_access_resource(cls, user_id: str, resource_owner_id: str, user_role: str, required_permission: str) -> bool:
        """Check if user can access a specific resource"""
        # Users can always access their own resources
        if user_id == resource_owner_id:
            return cls.has_permission(user_role, required_permission)
        
        # Admins can access all resources
        if user_role == 'admin':
            return True
        
        # Managers can read all resources
        if user_role == 'manager' and required_permission == 'read':
            return True
        
        return False


class SessionManager:
    """Session management utilities"""
    
    def __init__(self):
        self.active_sessions = {}  # In production, use Redis
    
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create user session"""
        session_id = f"session_{user_id}_{datetime.now().timestamp()}"
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc),
            'last_activity': datetime.now(timezone.utc),
            'data': session_data
        }
        
        logger.info("Session created", session_id=session_id, user_id=user_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session = self.active_sessions.get(session_id)
        
        if session:
            # Update last activity
            session['last_activity'] = datetime.now(timezone.utc)
            
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info("Session invalidated", session_id=session_id)
            return True
        
        return False
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions"""
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            age = now - session_data['last_activity']
            if age.total_seconds() > max_age_hours * 3600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info("Expired sessions cleaned up", count=len(expired_sessions))


# Global instances
auth_manager = AuthenticationManager()
role_access = RoleBasedAccess()
session_manager = SessionManager()


# FastAPI dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    return await auth_manager.get_current_user(credentials)


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to get current user if authenticated"""
    return await auth_manager.get_optional_user(request)


def require_permissions(permissions: List[str]):
    """FastAPI dependency to require specific permissions"""
    async def permission_checker(current_user: Dict[str, Any] = get_current_user) -> Dict[str, Any]:
        user_role = current_user.get('role', 'authenticated')
        
        for permission in permissions:
            if not role_access.has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão necessária: {permission}"
                )
        
        return current_user
    
    return permission_checker