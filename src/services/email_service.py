from typing import Dict, Any

from pydantic import EmailStr

from src.config.settings import settings
from pathlib import Path
from jose import jwt
from datetime import datetime, timedelta
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail, MessageType, fastmail

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates"  # Make sure this directory exists
)


async def send_email(
        email: str,
        subject: str,
        body: str,
        template_body: Dict[str, Any] = None
) -> None:
    """
    Send an email using FastMail

    Args:
        email: Recipient email address
        subject: Email subject
        body: Plain text body (fallback)
        template_body: Optional dictionary for HTML template variables
    """
    # Create message schema
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    await fm.send_message(message)

async def send_verification_email(email: EmailStr, token: str):
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    message = MessageSchema(
        subject="Verify your email address",
        recipients=[email],
        template_body={
            "verification_url": verification_url,
            "valid_hours": 48
        },
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="verification_email.html")


def create_verification_token(email: str) -> str:
    expiry = datetime.now() + timedelta(hours=48)
    token_data = {
        "email": email,
        "exp": expiry
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload["email"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None