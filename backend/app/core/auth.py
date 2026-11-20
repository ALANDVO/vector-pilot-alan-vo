from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette import status
from urllib.parse import urlparse

from backend.app.core.config import get_settings
from backend.app.models.user import User, Role
from backend.app.core.database import get_db, get_session_maker, Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def _parse_issuer_url() -> str:
    """Extract the issuer URL base from config."""
    settings = get_settings()
    issuer = settings.oidc_issuer_url
    if not issuer:
        return ""
    # Ensure no trailing slash
    return issuer.rstrip("/")


# OAuth2 scheme for Keycloak OpenID Discovery
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="",  # We'll handle token validation manually
    authorizationUrl="",
)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token in the Authorization header.
    
    Expected Authorization header format: Bearer <jwt_token>
    Validates: signature, issuer, audience
    Returns: User model if valid, raises HTTPException otherwise
    """
    authorization: Optional[str] = getattr(request, "authorization", None)
    if not authorization or not authorization.startswith("Bearer "):
        # In development mode without OIDC config, try to get or create a dummy user
        from backend.app.core.config import get_settings as _gs
        if not _gs().oidc_issuer_url:
            # Try to find or create a dev user
            result = await db.execute(select(User).where(User.keycloak_id == "dev-user"))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    keycloak_id="dev-user",
                    email="dev@localhost",
                    username="devuser",
                    role=Role.ANALYST,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[len("Bearer "):].strip()
    if not token:
        from backend.app.core.config import get_settings as _gs
        if not _gs().oidc_issuer_url:
            result = await db.execute(select(User).where(User.keycloak_id == "dev-user"))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    keycloak_id="dev-user",
                    email="dev@localhost",
                    username="devuser",
                    role=Role.ANALYST,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await _validate_jwt_token(token, db)


async def _validate_jwt_token(token: str, db: AsyncSession) -> User:
    """Validate a JWT token and return the associated user."""
    settings = get_settings()
    
    # If OIDC is not configured, skip validation (development mode)
    if not settings.oidc_issuer_url:
        # Try to find or create a dev user
        result = await db.execute(select(User).where(User.keycloak_id == "dev-user"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                keycloak_id="dev-user",
                email="dev@localhost",
                username="devuser",
                role=Role.ANALYST,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user
    
    issuer = settings.oidc_issuer_url.rstrip("/")
    audience = settings.oidc_audience or "vector-pilot-alan-vo"
    client_id = settings.oidc_client_id or "vector-pilot"
    
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(
            token,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
            },
            audience=audience,
            issuer=issuer,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract subject (sub) and roles from the token
    sub: str = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' field",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract roles from the token
    roles: list[str] = payload.get("realm_access", {}).get("roles", []) + payload.get("resource_access", {}).get(client_id, {}).get("roles", [])
    
    # Look up the user in the database by their keycloak_id (sub)
    stmt = select(User).where(User.keycloak_id == sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # User not found in local DB - create them
        # Determine role: first matching role or default to ANALYST
        user_role = Role.ANALYST
        if roles:
            role_name = roles[0]
            try:
                user_role = Role(role_name)
            except ValueError:
                user_role = Role.ANALYST
        
        user = User(
            keycloak_id=sub,
            email=payload.get("email", ""),
            username=payload.get("preferred_username", sub),
            role=user_role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Update user role based on token roles
    token_roles = set(payload.get("realm_access", {}).get("roles", [])) | set(payload.get("resource_access", {}).get(client_id, {}).get("roles", []))
    if token_roles:
        # Use the first suitable role from token, preferring higher privilege
        role_order = [Role.ADMIN, Role.OPERATOR, Role.ANALYST]
        best_role = Role.ANALYST
        for r in role_order:
            if r.value in token_roles:
                best_role = r
                break
        if user.role != best_role:
            user.role = best_role
            await db.commit()
    
    return user


def get_role_required(allowed_roles: list[Role]) -> callable:
    """Dependency factory that returns a role-checking dependency.
    
    Usage: Depends(get_role_required([Role.ADMIN, Role.OPERATOR]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}, Got: {current_user.role.value}",
            )
        return current_user
    return role_checker
