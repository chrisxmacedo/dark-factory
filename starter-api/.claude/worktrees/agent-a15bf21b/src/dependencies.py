from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.auth import (
    CurrentUser,
    RequireRole,
    RequireSupplierAccess,
    UserRole,
    get_current_user,
)

DB = Annotated[AsyncSession, Depends(get_db)]
RequireAuth = Annotated[CurrentUser, Depends(get_current_user)]

__all__ = [
    "CurrentUser",
    "DB",
    "RequireAuth",
    "RequireRole",
    "RequireSupplierAccess",
    "UserRole",
]
