from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel


class QuestionOption(BaseModel):
    id: UUID
    text: str
    is_correct: bool

class Question(BaseModel):
    id: UUID
    text: str
    options: List[QuestionOption]
    multiple_correct: bool

class QuizCreate(BaseModel):
    subject: str
    num_questions: int = 5

class QuizResponse(BaseModel):
    id: UUID
    subject: str
    questions: List[Question]
    created_at: datetime

class SubmitAnswer(BaseModel):
    question_id: UUID
    selected_option_ids: List[UUID]

class QuizSubmission(BaseModel):
    quiz_id: UUID
    answers: List[SubmitAnswer]

class QuizResult(BaseModel):
    id: UUID
    quiz_id: UUID
    user_id: UUID
    total_questions: int
    correct_answers: int
    score_percentage: float
    feedback: List[str]
    created_at: datetime