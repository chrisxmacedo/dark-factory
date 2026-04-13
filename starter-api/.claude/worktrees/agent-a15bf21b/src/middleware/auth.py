import enum
import uuid
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import get_settings

settings = get_settings()

bearer_scheme = HTTPBearer()


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    SUPPLIER = "supplier"
    CONSUMER = "consumer"


class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None
    supplier_id: str | None = None
    app_metadata: dict[str, Any] | None = None


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str | None = None
    role: UserRole
    supplier_id: uuid.UUID | None = None


def _auth_error(detail: str) -> Exception:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_jwt(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise _auth_error("Invalid or expired token") from e


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> CurrentUser:
    payload = verify_jwt(credentials.credentials)

    # Prefer app_metadata claims (set by admin), fall back to top-level
    meta = payload.app_metadata or {}
    raw_role = meta.get("role") or payload.role
    raw_supplier_id = meta.get("supplier_id") or payload.supplier_id

    try:
        role = UserRole(raw_role) if raw_role else UserRole.CONSUMER
    except ValueError:
        role = UserRole.CONSUMER

    supplier_id = None
    if raw_supplier_id:
        try:
            supplier_id = uuid.UUID(str(raw_supplier_id))
        except ValueError:
            pass

    return CurrentUser(
        id=uuid.UUID(payload.sub),
        email=payload.email,
        role=role,
        supplier_id=supplier_id,
    )


class RequireRole:
    """Dependency that checks the user has one of the allowed roles."""

    def __init__(self, *allowed_roles: UserRole) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' is not permitted. "
                    f"Required: {', '.join(r.value for r in self.allowed_roles)}"
                ),
            )
        return current_user


class RequireSupplierAccess:
    """Dependency that ensures the user can access a specific supplier's data."""

    def __call__(
        self,
        request: Request,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role == UserRole.ADMIN:
            return current_user

        if current_user.role == UserRole.CONSUMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consumer role is read-only",
            )

        if current_user.role == UserRole.SUPPLIER:
            supplier_id_str = request.path_params.get("supplier_id")
            if supplier_id_str:
                try:
                    path_supplier_id = uuid.UUID(str(supplier_id_str))
                except ValueError:
                    pass
                else:
                    if current_user.supplier_id != path_supplier_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only access your own supplier data",
                        )

        return current_user


RequireAuth = Annotated[CurrentUser, Depends(get_current_user)]
