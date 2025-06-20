from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime

class InterviewCreate(BaseModel):
    role: str

class QuestionRubric(BaseModel):
    excellent: str
    good: str
    average: str
    poor: str

class Question(BaseModel):
    id: UUID4
    text: str
    category: str
    expected_duration: int
    rubric: QuestionRubric

class InterviewResponse(BaseModel):
    id: UUID4
    role: str
    questions: List[Question]
    created_at: datetime

class Recording(BaseModel):
    question_id: UUID4
    video_url: str
    feedback: Optional[str] = None

class InterviewAttemptCreate(BaseModel):
    interview_id: UUID4
    recordings: List[Recording]

class InterviewAttemptResponse(BaseModel):
    id: UUID4
    interview_id: UUID4
    user_id: UUID4
    recordings: List[Recording]
    created_at: datetime

    class Config:
        orm_mode = True