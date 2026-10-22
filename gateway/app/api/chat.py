from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_pipeline
from app.models.schemas import ChatRequest, ChatResponse
from app.pipeline import SecurityPipeline


router = APIRouter(tags=["inference"])


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    pipeline: SecurityPipeline = Depends(get_pipeline),
) -> ChatResponse:
    try:
        return await pipeline.process(request)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The inference provider is unavailable and offline fallback is disabled.",
        ) from exc

