from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["discovery"])


@router.get(
    "/schema",
    summary="OpenAPI schema",
    description=(
        "Returns the full OpenAPI schema for this API as JSON. "
        "AI agents and clients can use this endpoint to self-discover "
        "all available operations, parameters, and response shapes at runtime."
    ),
    include_in_schema=True,
    response_class=JSONResponse,
)
async def get_schema(request: Request) -> JSONResponse:
    return JSONResponse(request.app.openapi())
