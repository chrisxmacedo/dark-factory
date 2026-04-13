from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(
        description="API health status. Always 'ok' when the API is running.",
        examples=["ok"],
    )
    version: str = Field(
        description="Current API version.",
        examples=["0.1.0"],
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description=(
        "Returns 200 if the API is running and healthy. "
        "AI agents should call this endpoint before starting a session "
        "to verify the API is available. No authentication required."
    ),
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "version": "0.1.0"}
                }
            },
        }
    },
    openapi_extra={
        "x-agent-hints": {
            "idempotent": True,
            "auth_required": False,
            "use_for": "Verify API availability before starting a session",
        }
    },
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")

