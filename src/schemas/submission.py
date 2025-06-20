from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum
from uuid import UUID
from pydantic import BaseModel, Field


class SubmissionType(str, PyEnum):
    ASSIGNMENT = "assignment"
    PROJECT = "project"



class FileResponse(BaseModel):
    filename: str
    file_path: str
    file_type: str

    class Config:
        from_attributes = True


class SubmissionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: SubmissionType
    description: str = Field(..., min_length=1)


class SubmissionCreate(BaseModel):
    title: str
    type: SubmissionType
    description: str

class SubmissionCreateWithCourse(SubmissionCreate):
    course_name: str
    course_id: str
    dept: str
    due_date: datetime

class CommentCreate(BaseModel):
    content: str



class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True




class SubmissionResponse(BaseModel):
    id: UUID
    type: SubmissionType
    title: str
    description: Optional[str]
    created_at: datetime
    user_id: UUID
    files: List[FileResponse]

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: UUID
    username: str

    class Config:
        from_attributes = True

class SubmissionResponseWithCourse(SubmissionResponse):
    course_name: str
    course_id: str
    dept: str
    due_date: datetime

    class Config:
        from_attributes = True


class UpdateSubmission(BaseModel):
    title: Optional[str] = None
    type: Optional[SubmissionType] = None
    description: Optional[str] = None
    course_name: Optional[str] = None
    course_id: Optional[str] = None
    dept: Optional[str] = None
    due_date: Optional[datetime] = None

