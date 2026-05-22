from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.inference_log import InferenceLog
from app.schemas.inference_log import InferenceLogListResponse, InferenceLogResponse, MetricsResponse
from app.services import get_metrics

router = APIRouter()

@router.get("/logs", response_model=InferenceLogListResponse)
async def list_logs(provider: str = Query(None), status: str = Query(None), start_date: str = Query(None), end_date: str = Query(None), limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)):
    q = select(InferenceLog)
    if provider: q = q.where(InferenceLog.provider == provider)
    if status: q = q.where(InferenceLog.status == status)
    if start_date: q = q.where(InferenceLog.created_at >= start_date)
    if end_date: q = q.where(InferenceLog.created_at <= end_date)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(InferenceLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    logs = list(result.scalars().all())
    return InferenceLogListResponse(logs=[InferenceLogResponse.model_validate(log) for log in logs], total=total)

@router.get("/logs/metrics", response_model=MetricsResponse)
async def get_log_metrics(window: str = Query("24h"), db: AsyncSession = Depends(get_db)):
    if window not in {"1h", "6h", "24h", "7d"}: raise HTTPException(status_code=400, detail="Window must be: 1h, 6h, 24h, 7d")
    metrics = await get_metrics(db, window=window)
    return MetricsResponse(**metrics)
