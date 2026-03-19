from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import base64
from app.database import get_db
from app.models.qrcode import QRCode
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.generator import generate_qr, get_ai_suggestion
from app.config import settings

router = APIRouter(prefix="/api/qrcodes", tags=["qrcodes"])


class QRCreate(BaseModel):
    content: str
    content_type: str = "url"
    fg_color: str = "#000000"
    bg_color: str = "#FFFFFF"
    size: int = 300
    logo_url: Optional[str] = None
    title: Optional[str] = None


class QRResponse(BaseModel):
    id: int
    content: str
    content_type: str
    fg_color: str
    bg_color: str
    size: int
    logo_url: Optional[str]
    title: Optional[str]
    description: Optional[str]
    ai_suggestion: Optional[str]
    scan_count: int
    image_base64: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=QRResponse, status_code=status.HTTP_201_CREATED)
async def create_qrcode(
    payload: QRCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_premium:
        count_result = await db.execute(
            select(func.count()).where(QRCode.user_id == current_user.id)
        )
        qr_count = count_result.scalar()
        if qr_count >= settings.FREE_QR_LIMIT:
            raise HTTPException(status_code=403, detail=f"Free plan limited to {settings.FREE_QR_LIMIT} QR codes. Upgrade to premium.")

    image_base64 = generate_qr(
        content=payload.content,
        fg_color=payload.fg_color,
        bg_color=payload.bg_color,
        size=payload.size,
        logo_url=payload.logo_url,
    )

    ai_suggestion = await get_ai_suggestion(payload.content, payload.content_type)

    qr = QRCode(
        user_id=current_user.id,
        content=payload.content,
        content_type=payload.content_type,
        fg_color=payload.fg_color,
        bg_color=payload.bg_color,
        size=payload.size,
        logo_url=payload.logo_url,
        title=payload.title,
        ai_suggestion=ai_suggestion,
    )
    db.add(qr)
    current_user.total_qrcodes += 1
    await db.commit()
    await db.refresh(qr)

    result = qr.__dict__.copy()
    result["image_base64"] = image_base64
    return result


@router.get("/", response_model=List[QRResponse])
async def list_qrcodes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QRCode).where(QRCode.user_id == current_user.id).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{qr_id}/image")
async def get_qr_image(
    qr_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id, QRCode.user_id == current_user.id))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")

    image_base64 = generate_qr(
        content=qr.content,
        fg_color=qr.fg_color,
        bg_color=qr.bg_color,
        size=qr.size,
        logo_url=qr.logo_url,
    )
    image_bytes = base64.b64decode(image_base64)
    return Response(content=image_bytes, media_type="image/png")


@router.get("/{qr_id}/stats")
async def get_qr_stats(
    qr_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id, QRCode.user_id == current_user.id))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    return {"qr_id": qr_id, "scan_count": qr.scan_count, "title": qr.title, "content_type": qr.content_type}


@router.post("/{qr_id}/scan")
async def record_scan(qr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id, QRCode.is_active == True))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    qr.scan_count += 1
    if qr.user_id:
        user_result = await db.execute(select(User).where(User.id == qr.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.total_scans += 1
    await db.commit()
    return {"status": "recorded", "scan_count": qr.scan_count}


@router.delete("/{qr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qrcode(
    qr_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id, QRCode.user_id == current_user.id))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    await db.delete(qr)
    await db.commit()
