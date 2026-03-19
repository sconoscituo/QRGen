"""
QR코드 스캔 분석 라우터
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["QR 분석"])

try:
    from app.models.qrcode import QRCode
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    from app.models.scan_log import ScanLog
    HAS_SCAN = True
except ImportError:
    HAS_SCAN = False


@router.get("/qrcodes/{qr_id}")
async def get_qr_analytics(
    qr_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """QR코드 스캔 통계 조회"""
    if not HAS_QR:
        return {"message": "QR 모델이 없습니다"}

    result = await db.execute(
        select(QRCode).where(
            QRCode.id == qr_id,
            QRCode.user_id == current_user.id
        )
    )
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(404, "QR코드를 찾을 수 없습니다")

    scan_count = getattr(qr, "scan_count", 0) or 0
    created_at = getattr(qr, "created_at", datetime.utcnow())
    days_active = (datetime.utcnow() - created_at).days or 1

    return {
        "qr_id": qr_id,
        "total_scans": scan_count,
        "days_active": days_active,
        "avg_daily_scans": round(scan_count / days_active, 2),
        "url": getattr(qr, "url", ""),
        "created_at": str(created_at),
    }


@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """전체 QR코드 통계 요약"""
    if not HAS_QR:
        return {"qr_codes": 0, "total_scans": 0}

    result = await db.execute(
        select(
            func.count(QRCode.id).label("total_qr"),
            func.sum(QRCode.scan_count).label("total_scans"),
        ).where(QRCode.user_id == current_user.id)
    )
    row = result.one()
    return {
        "total_qr_codes": row.total_qr or 0,
        "total_scans": int(row.total_scans or 0),
        "avg_scans_per_qr": round((row.total_scans or 0) / max(row.total_qr or 1, 1), 1),
    }
