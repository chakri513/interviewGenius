import random
import string
from datetime import datetime, timedelta, timezone
from traceback import print_tb

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.config.settings import settings
from src.db.db import get_db
from src.db.models import User
from src.schemas.user_schema import EmailRequest
from src.schemas.user_schema import EmailSchema
from src.schemas.user_schema import EmailUpdate
from src.schemas.user_schema import OTPVerify, PasswordReset
from src.schemas.user_schema import UserCreate
from src.services.auth_service import get_current_user
from src.services.auth_service import verify_password, get_password_hash, create_access_token
from src.services.email_service import send_email
from src.services.email_service import send_verification_email, create_verification_token, verify_token
from starlette.responses import RedirectResponse

from app.src.services.auth_service import decode_token

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Initial registration without face data"""
    try:
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        verification_token = create_verification_token(user.email)

        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            university=user.university,
            semester=user.semester,
            mobile=user.mobile,
            alt_mobile=user.alt_mobile,
            verification_code=verification_token,
            # use_face_login=False
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        await send_verification_email(user.email, verification_token)

        return {
            "message": "Registration successful. Please check your email to verify your account."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# @router.post("/register-face")
# async def register_face(face_data: FaceRegistrationRequest, db: Session = Depends(get_db)):
#     """Register face data for existing user"""
#     try:
#         user = db.query(User).filter(User.email == face_data.email).first()
#         if not user:
#             raise HTTPException(
#                 status_code=404,
#                 detail="User not found"
#             )
#
#         # Decode base64 image
#         image_data = base64.b64decode(face_data.face_data.split(',')[1])
#         nparr = np.frombuffer(image_data, np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#
#         # Convert BGR to RGB
#         rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#
#         # Detect face and get encoding
#         face_locations = face_recognition.face_locations(rgb_img)
#         if not face_locations:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No face detected in the image"
#             )
#
#         face_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
#
#         # Store face encoding
#         user.face_encoding = face_encoding.tobytes()
#         user.use_face_login = True
#         db.commit()
#
#         return {"message": "Face registration successful"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error registering face: {str(e)}"
#         )
#
# @router.post("/login/method")
# async def choose_login_method(
#     login_data: LoginMethod,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == login_data.email).first()
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )
#
#     if not user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Please verify your email before logging in"
#         )
#
#     return {
#         "available_methods": {
#             "normal_login": True,
#             "face_login": user.use_face_login
#         }
#     }
#


@router.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )

    user.is_verified = True
    user.verification_token = None
    user.token_expiry = None
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}



@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email already verified"
            )

        verification_token = create_verification_token(email)
        token_expiry = datetime.now() + timedelta(hours=48)

        user.verification_code = verification_token
        db.commit()

        await send_verification_email(email, verification_token)
        return {"message": "Verification email resent successfully"}
    except Exception as e:
        print_tb(e.__traceback__)  # This will print the full traceback
        return {"error": str(e)}


@router.post("/update-email")
async def update_email(
        email_update: EmailUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(email_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Check if new email already exists
    if db.query(User).filter(User.email == email_update.new_email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create verification token for new email
    verification_token = create_verification_token(email_update.new_email)

    # Store temporary email change request
    current_user.pending_email = email_update.new_email
    current_user.email_verification_token = verification_token
    current_user.email_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    # Send verification email to new address
    await send_email(
        email_update.new_email,
        "Verify Your New Email",
        f"Please click the following link to verify your new email address: "
        f"{settings.BASE_URL}/auth/verify-email-update/{verification_token}"
    )

    return {"message": "Please check your new email address for verification instructions"}


@router.get("/verify-email-update/{token}")
async def verify_email_update(token: str, db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    user = db.query(User).filter(User.pending_email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email update request not found"
        )

    if datetime.utcnow() > user.email_token_expiry:
        raise HTTPException(
            status_code=400,
            detail="Verification token has expired"
        )

    # Update email
    user.email = user.pending_email
    user.pending_email = None
    user.email_verification_token = None
    user.email_token_expiry = None
    db.commit()

    return {"message": "Email updated successfully"}


@router.post("/forgot-password")
async def forgot_password(email_data: EmailSchema, db: Session = Depends(get_db)):
    email = email_data.email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If the email exists, password reset instructions will be sent"}

    reset_token = create_verification_token(email)

    # Store reset token
    user.password_reset_token = reset_token
    user.password_reset_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    # Send reset email
    await send_email(
        email,
        "Password Reset Request",
        f"Please click the following link to reset your password: "
        f"{settings.FRONTEND_URL}/auth/reset-password/{reset_token}"
    )

    return {"message": "Password reset instructions sent to your email"}


@router.post("/reset-password/{token}")
async def reset_password(token: str, new_password: PasswordReset, db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset request"
        )

    if datetime.utcnow() > user.password_reset_expiry:
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired"
        )

    # Update password
    user.hashed_password = get_password_hash(new_password.password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    db.commit()

    return {"message": "Password reset successful"}


# 2-Step Authentication with Email OTP

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))



@router.post("/resend-otp")
async def resend_otp(email_request: EmailRequest, db: Session = Depends(get_db)):
    try:
        # Fetch the user from the database
        user = db.query(User).filter(User.email == email_request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate a new OTP
        new_otp = generate_otp()
        otp_expiry = datetime.now() + timedelta(minutes=15)  # Set expiry time

        # Update the OTP and expiry in the database
        user.login_otp = new_otp
        user.otp_expiry = otp_expiry
        db.commit()
        print(user.email)
        # Send the OTP to the user's email
        send_email(user.email,
        "Login OTP",
        f"Your OTP for login is: {new_otp}. This OTP will expire in 15 minutes.")

        print(f"Debug - New OTP: {new_otp}")
        print(f"Debug - New OTP expiry time: {otp_expiry}")

        return {"message": "OTP resent successfully. Please check your email."}
    except Exception as e:
        print(f"Debug - Error in resend_otp: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not resend OTP")

@router.post("/token", response_model=dict)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in"
        )
    otp = generate_otp()
    user.login_otp = otp
    user.otp_expiry = datetime.now() + timedelta(minutes=15)
    db.commit()

    print(f"Debug - Generated OTP: {otp}")
    print(f"Debug - OTP expiry set to: {user.otp_expiry}")

    await send_email(
        user.email,
        "Login OTP",
        f"Your OTP for login is: {otp}. This OTP will expire in 15 minutes."
    )

    return {
        "message": "Please check your email for OTP",
        "requires_otp": True,
        "email": user.email
    }


@router.post("/verify-otp")
async def verify_otp(request: Request, otp_data: OTPVerify, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == otp_data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"Debug - Received OTP: {otp_data.otp}")
        print(f"Debug - Stored OTP: {user.login_otp}")
        print(f"Debug - Current time UTC: {datetime.utcnow()}")
        print(f"Debug - OTP expiry time: {user.otp_expiry}")

        if not user.login_otp or user.login_otp != otp_data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        current_time_utc = datetime.now(timezone.utc)
        otp_expiry_time = user.otp_expiry

        if current_time_utc > otp_expiry_time:
            print(f"Debug - OTP expired at {otp_expiry_time}")
            raise HTTPException(status_code=400, detail="OTP has expired")

        # Clear OTP
        user.login_otp = None
        user.otp_expiry = None
        db.commit()

        # Create token
        access_token = create_access_token(data={"sub": user.email})

        # Set session - remove the .modified attribute
        request.session["access_token"] = access_token

        print(f"Debug - Token created and stored: {access_token}")
        print(f"Debug - Session after token storage: {dict(request.session)}")

        return {
            "message": "Login successful",
            "access_token": access_token,

        }
    except Exception as e:
        print(f"Debug - Error in verify_otp: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/logout")
async def logout(request:Request,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Logout the currently authenticated user by invalidating their session/token.
    """
    try:
        access_token = request.session.get("access_token")
        print("Debug - Retrieved token:", access_token)

        if not access_token:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

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

        user.login_otp = None
        user.otp_expiry = None
        db.commit()
        del request.session["access_token"]

        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during logout: {str(e)}"
        )