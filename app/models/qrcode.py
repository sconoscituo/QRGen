from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class QRCode(Base):
    __tablename__ = "qrcodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="url")  # url, text, contact, wifi
    fg_color = Column(String(20), default="#000000")
    bg_color = Column(String(20), default="#FFFFFF")
    size = Column(Integer, default=300)
    logo_url = Column(String(512), nullable=True)
    image_path = Column(String(512), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    ai_suggestion = Column(Text, nullable=True)
    scan_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="qrcodes")
