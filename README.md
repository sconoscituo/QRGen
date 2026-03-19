# QRGen

AI QR code generator with design customization.

## Features

- QR code generation for URL, text, contact, WiFi
- Foreground/background color customization
- Logo insertion support
- Size customization
- Gemini AI: usage suggestions for each QR code
- Scan count tracking
- JWT authentication
- Free (10 QR codes) and Premium plans

## Quick Start

```bash
cp .env.example .env
# Edit .env with your settings

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

## Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/users/register | Register |
| POST | /api/users/login | Login |
| GET | /api/users/me | Profile |
| POST | /api/qrcodes/ | Generate QR code |
| GET | /api/qrcodes/ | List my QR codes |
| GET | /api/qrcodes/{id}/image | Download PNG |
| GET | /api/qrcodes/{id}/stats | Scan stats |
| POST | /api/qrcodes/{id}/scan | Record scan |
| DELETE | /api/qrcodes/{id} | Delete QR code |
| GET | /api/payments/plans | View plans |
| POST | /api/payments/create | Create payment |
| POST | /api/payments/confirm | Confirm payment |

## Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | SQLite async URL |
| SECRET_KEY | JWT signing key |
| GEMINI_API_KEY | Google Gemini API key |
| QR_STORAGE_PATH | Directory for saved QR images |
| FREE_QR_LIMIT | Max QR codes for free users |
