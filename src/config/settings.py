from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):

    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str = "your_jwt_secret_key"
    OAUTH2_CLIENT_ID: str = "6383524796"
    OAUTH2_CLIENT_SECRET: str = "Hemanth888"
    OAUTH2_AUTHORIZATION_URL: str = "http://localhost:8007/oauth2/authorize"
    OAUTH2_TOKEN_URL: str = "http://localhost:8007/oauth2/token"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAIL_USERNAME: str = "contact.interviewgenius@gmail.com"
    MAIL_PASSWORD: str = "byhr cxgm ujoj ggbo"
    MAIL_FROM: str = "contact.interviewgenius@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    BASE_URL: str = "http://localhost:8007"
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

