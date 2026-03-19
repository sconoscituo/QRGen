import qrcode
from PIL import Image
import io
import base64
import os
import uuid
from typing import Optional
import google.generativeai as genai
from app.config import settings


def _init_gemini():
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel("gemini-1.5-flash")
    return None


def generate_qr(
    content: str,
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    size: int = 300,
    logo_url: Optional[str] = None,
) -> str:
    """Generate QR code and return base64 encoded PNG."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    if logo_url:
        try:
            import httpx
            response = httpx.get(logo_url, timeout=5.0)
            if response.status_code == 200:
                logo = Image.open(io.BytesIO(response.content)).convert("RGBA")
                logo_size = size // 4
                logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
                pos = ((size - logo_size) // 2, (size - logo_size) // 2)
                img.paste(logo, pos, logo)
        except Exception:
            pass

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def save_qr_to_file(content: str, fg_color: str = "#000000", bg_color: str = "#FFFFFF", size: int = 300) -> str:
    """Generate QR code and save to file, returning file path."""
    os.makedirs(settings.QR_STORAGE_PATH, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(settings.QR_STORAGE_PATH, filename)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg_color, back_color=bg_color)
    img = img.resize((size, size), Image.LANCZOS)
    img.save(filepath, format="PNG")
    return filepath


async def get_ai_suggestion(content: str, content_type: str) -> Optional[str]:
    """Use Gemini to generate usage suggestions for the QR code."""
    model = _init_gemini()
    if not model:
        return None

    prompt = f"""You are a QR code expert. Given the following QR code content, provide:
1. A brief description of what this QR code does (1 sentence)
2. Two practical use cases for this QR code

Content type: {content_type}
Content: {content[:500]}

Respond in 3 sentences max."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None
