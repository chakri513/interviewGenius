import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey, Integer, JSON, LargeBinary, func, \
    ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from src.schemas.submission import SubmissionType

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    university = Column(String)
    semester = Column(Integer)
    mobile = Column(String, unique=True)
    alt_mobile = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    pending_email = Column(String)
    email_verification_token = Column(String)
    email_token_expiry = Column(DateTime)
    # For password reset
    password_reset_token = Column(String)
    password_reset_expiry = Column(DateTime)

    # For 2FA/OTP
    login_otp = Column(String)
    otp_expiry = Column(DateTime(timezone=True))
    interview_attempts = relationship("InterviewAttempt", back_populates="user")



class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(Enum(SubmissionType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_name = Column(String)
    course_id = Column(String)
    dept = Column(String)
    due_date = Column(DateTime)

    # Relationships
    files = relationship("SubmissionFile", back_populates="submission")
    comments = relationship("Comment", back_populates="submission")


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.now)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)

    # Relationship
    submission = relationship("Submission", back_populates="files")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)

    # Relationships
    submission = relationship("Submission", back_populates="comments")


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject = Column(String, index=True)
    questions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    quiz_id =  Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    user_id =  Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    answers = Column(JSON)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)




class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role = Column(String, nullable=False)
    questions = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    attempts = relationship("InterviewAttempt", back_populates="interview")


class InterviewAttempt(Base):
    __tablename__ = "interview_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recordings = Column(JSON, nullable=False)  # Store video URLs and feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    interview = relationship("Interview", back_populates="attempts")
    user = relationship("User", back_populates="interview_attempts")


class InterviewAnalysis(Base):
    __tablename__ = "interview_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("interview_attempts.id"))
    emotion_analysis = Column(JSONB)
    pose_analysis = Column(JSONB)
    speech_analysis = Column(JSONB)
    behavioral_insights = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class InterviewFeedback(Base):
    """
    Model for storing AI-generated and manual feedback for interview attempts
    """
    __tablename__ = "interview_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID, ForeignKey("interview_attempts.id"), nullable=False)
    detailed_feedback = Column(String, nullable=True)
    improvement_areas = Column(ARRAY(String), nullable=True)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.utcnow, nullable=False)
