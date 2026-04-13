from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.auth import CurrentUser, get_current_user

# Reusable dependency type aliases — import these in routers
DB = Annotated[AsyncSession, Depends(get_db)]
RequireAuth = Annotated[CurrentUser, Depends(get_current_user)]
