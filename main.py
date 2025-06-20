import os

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from src.services.auth_service import get_current_user, decode_token
from src.routers import dashboard
from src.routers import auth_router
from src.routers import quiz_router
from src.routers import interview
from src.db.db import engine, get_db
from src.db.models import Base, User

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Registration API")

from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="your-secure-secret-key",
    session_cookie="session",
    max_age=3600,
    same_site="lax",
    https_only=False
)


app.include_router(auth_router.router, tags=["authentication"])
app.include_router(interview.interview_router, tags=["interview"])
app.include_router(dashboard.submission_router,tags=["dashboard"])
app.include_router(quiz_router.quiz_router,tags=["quiz"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "src/templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/mock-interview")
async def register_page(request: Request):
    return templates.TemplateResponse("interview.html", {"request": request})

@app.get("/password-reset")
async def password_reset(request: Request):
    return templates.TemplateResponse("password_reset.html", {"request": request})

@app.get("/quiz")
async def quiz(request: Request):
    print("Debug - Full session data:", dict(request.session))

    access_token = request.session.get("access_token")
    print("Debug - Retrieved token:", access_token)

    if not access_token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("quiz.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request):
    print("Debug - Full session data:", dict(request.session))

    access_token = request.session.get("access_token")
    print("Debug - Retrieved token:", access_token)

    if not access_token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    try:
        email = decode_token(access_token)
        print("Debug - Token payload:", email)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return templates.TemplateResponse(
            "dashboard-1.html",
            {
                "request": request,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_verified
                }
            }
        )
    except Exception as e:
        print(f"Debug - Dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", reload=True, port=8007)