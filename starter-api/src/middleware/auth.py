import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import get_settings

settings = get_settings()

bearer_scheme = HTTPBearer()


class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str | None = None
    role: str | None = None


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> CurrentUser:
    payload = verify_jwt(credentials.credentials)
    return CurrentUser(
        id=uuid.UUID(payload.sub),
        email=payload.email,
        role=payload.role,
    )


# Dependency aliases
RequireAuth = Annotated[CurrentUser, Depends(get_current_user)]
