from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from uuid import uuid4, UUID
import json
from datetime import datetime
from pydantic import BaseModel, validator, Field, field_validator
from sqlalchemy.orm import Session
from src.db.models import User, InterviewAttempt, Interview, InterviewFeedback
from src.db.db import get_db
from src.services.auth_service import get_current_user, decode_token
import google.generativeai as genai
from starlette import status
from starlette.responses import RedirectResponse


# Schema definitions
class QuestionResponse(BaseModel):
    id: UUID
    text: str
    category: str
    expected_duration: int
    rubric: dict

class InterviewResponse(BaseModel):
    id: UUID
    role: str
    questions: List[QuestionResponse]
    created_at: datetime

class Answer(BaseModel):
    question_id: str = Field(..., description="The UUID of the question being answered")
    text: str = Field(..., description="The text of the answer")
    duration: int = Field(..., ge=0, description="Duration in seconds")

    @validator('question_id')
    def validate_uuid(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')

class InterviewSubmission(BaseModel):
    interview_id: str = Field(..., description="The UUID of the interview")
    recordings: List[Answer] = Field(..., min_items=1, description="List of answers")

    @field_validator('interview_id')
    def validate_interview_uuid(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid interview UUID format')

    class Config:
        schema_extra = {
            "example": {
                "interview_id": "123e4567-e89b-12d3-a456-426614174000",
                "recordings": [
                    {
                        "question_id": "123e4567-e89b-12d3-a456-426614174001",
                        "text": "Sample answer text",
                        "duration": 60
                    }
                ]
            }
        }
class FeedbackRequest(BaseModel):
    attempt_id: UUID
    detailed_feedback: Optional[str] = None
    improvement_areas: Optional[List[str]] = None
    overall_score: Optional[float] = None

# Initialize Gemini Pro
genai.configure(api_key='AIzaSyCuDaMhFlW1C_-MZAbyOQ6XFpfVS2plSfk')
model = genai.GenerativeModel('gemini-1.5-flash')

INTERVIEW_PROMPT_TEMPLATE = """
Create an interview question set for the role: {role} with {num_questions} questions.
The questions should test both technical skills and behavioral aspects.
The response should be strictly in the following JSON format:
{{
    "questions": [
        {{
            "text": "question text",
            "category": "technical/behavioral",
            "expected_duration": 120,
            "rubric": {{
                "excellent": "Criteria for excellent response",
                "good": "Criteria for good response",
                "average": "Criteria for average response",
                "poor": "Criteria for poor response"
            }}
        }}
    ]
}}
Focus on questions that can be effectively answered in 2-3 minutes.
For technical questions, emphasize conceptual understanding and problem-solving approach rather than coding specifics.
Include behavioral questions that assess communication skills and experience.
"""

FEEDBACK_GENERATION_PROMPT = """
Analyze the following interview responses for a {role} position. Each response includes:
- The question asked
- The candidate's answer
- Time taken to respond
- The question category (technical/behavioral)
- The scoring rubric should be 0 or 1 only if its corect or wrong 

Question-Answer Pairs:
{qa_pairs}

Please evaluate:
1. Answer quality based on the rubric
2. Time management (comparing actual vs expected duration)
3. Technical competency
4. Communication clarity
5. Overall performance

Format the response as JSON:
{{
    "detailed_feedback": "comprehensive analysis of responses",
    "improvement_areas": ["area1", "area2", ...],
    "overall_score": float,
    "question_evaluations": [
        {{
            "question": "question text",
            "evaluation": "detailed evaluation",
            "score": float,
            "time_management": "evaluation of response timing"
        }},
        ...
    ]
}}
"""

interview_router = APIRouter(prefix="/interview", tags=["interview"])

@interview_router.post("/generate", response_model=InterviewResponse)
async def generate_interview(
        role: str,
        db=Depends(get_db)
):
    """Generate a new interview with questions"""
    try:
        prompt = INTERVIEW_PROMPT_TEMPLATE.format(
            role=role,
            num_questions=10
        )
        response = model.generate_content(prompt)
        print(response)
        content_text = response.text.strip()
        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.endswith("```"):
            if content_text.endswith("```"):
                content_text = content_text[:-3]
            content_text = content_text.strip()
            content = json.loads(content_text)
            if "questions" not in content or not isinstance(content["questions"], list):
                raise ValueError("Invalid response format from Gemini")
            processed_questions = []
            for question in content["questions"]:
                question_id = uuid4()
                processed_questions.append({
                    "id": str(question_id),
                    "text": question["text"],
                    "category": question["category"],
                    "expected_duration": question["expected_duration"],
                    "rubric": question["rubric"]
                })

            interview_id = uuid4()
            db_interview = Interview(
                id=interview_id,
                role=role,
                questions=processed_questions,
                created_at=datetime.utcnow()
            )
            db.add(db_interview)
            db.commit()
            db.refresh(db_interview)

            return InterviewResponse(
                id=interview_id,
                role=role,
                questions=processed_questions,
                created_at=db_interview.created_at
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate interview: {str(e)}")


@interview_router.post("/submit")
async def submit_interview(
        request: Request,
        submission: InterviewSubmission,
        db: Session = Depends(get_db)
):
    """Submit interview answers with timing information"""
    try:
        # Convert string UUID to UUID object for database query
        interview_id = UUID(submission.interview_id)
        interview = db.query(Interview).filter(Interview.id == interview_id).first()

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        access_token = request.session.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        email = decode_token(access_token)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create attempt record with recordings
        attempt = InterviewAttempt(
            id=uuid4(),
            interview_id=interview_id,
            user_id=user.id,
            recordings=[{
                "question_id": recording.question_id,
                "text": recording.text,
                "duration": recording.duration
            } for recording in submission.recordings],

        )

        db.add(attempt)
        db.commit()

        # Prepare QA pairs for feedback generation
        qa_pairs = []
        questions_dict = {str(q["id"]): q for q in interview.questions}

        for recording in submission.recordings:
            question = questions_dict.get(recording.question_id)
            if question:
                qa_pairs.append({
                    "question": question["text"],
                    "answer": recording.text,
                    "duration": recording.duration,
                    "expected_duration": question["expected_duration"],
                    "category": question["category"],
                    "rubric": question["rubric"]
                })

        # Generate feedback
        feedback_prompt = FEEDBACK_GENERATION_PROMPT.format(
            role=interview.role,
            qa_pairs=json.dumps(qa_pairs, indent=2)
        )
        feedback_response = model.generate_content(feedback_prompt)
        content_text = feedback_response.text.strip()
        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.endswith("```"):
            if content_text.endswith("```"):
                content_text = content_text[:-3]
            content_text = content_text.strip()
        print(feedback_response)
        try:
            feedback_content = json.loads(content_text)
            db_feedback = InterviewFeedback(
                id=uuid4(),
                attempt_id=attempt.id,
                detailed_feedback=feedback_content['detailed_feedback'],
                improvement_areas=feedback_content['improvement_areas'],
                overall_score=feedback_content['overall_score']
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing feedback: {str(e)}")
            db_feedback = InterviewFeedback(
                id=uuid4(),
                attempt_id=attempt.id,
                detailed_feedback=feedback_response.text,
                overall_score=None
            )

        db.add(db_feedback)
        db.commit()

        return {
            "message": "Interview submitted successfully",
            "attempt_id": str(attempt.id),
            "feedback_available": True
        }

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except Exception as e:
        print(f"Error in submit_interview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit interview: {str(e)}"
        )

@interview_router.get("/attempt/{attempt_id}/feedback")
async def get_interview_feedback(request:Request,
        attempt_id: UUID,
        db: Session = Depends(get_db),

):
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

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        """Retrieve feedback for a specific interview attempt"""
        attempt = db.query(InterviewAttempt).filter(
            InterviewAttempt.id == attempt_id,
            InterviewAttempt.user_id == user.id
        ).first()

        if not attempt:
            raise HTTPException(status_code=404, detail="Interview attempt not found")

        feedback = db.query(InterviewFeedback).filter(
            InterviewFeedback.attempt_id == attempt_id
        ).first()

        if not feedback:
            raise HTTPException(status_code=404, detail="No feedback available for this interview attempt")

    except Exception as e:
        print(str(e))

    return {
        "detailed_feedback": feedback.detailed_feedback,
        "improvement_areas": feedback.improvement_areas,
        "overall_score": feedback.overall_score,
    }

@interview_router.get("/history")
async def get_interview_history(request:Request,
        db: Session = Depends(get_db)
):
    """Get user's interview history with associated feedback"""
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

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    attempts = db.query(InterviewAttempt, Interview, InterviewFeedback).join(
        Interview,
        InterviewAttempt.interview_id == Interview.id
    ).outerjoin(
        InterviewFeedback,
        InterviewAttempt.id == InterviewFeedback.attempt_id
    ).filter(
        InterviewAttempt.user_id == user.id
    ).order_by(InterviewAttempt.submitted_at.desc()).all()

    history = []
    for attempt, interview, feedback in attempts:
        history.append({
            "id": attempt.id,
            "role": interview.role,
            "submitted_at": attempt.submitted_at,
            "answers": attempt.answers,
            "feedback": {
                "detailed_feedback": feedback.detailed_feedback if feedback else None,
                "improvement_areas": feedback.improvement_areas if feedback else None,
                "overall_score": feedback.overall_score if feedback else None
            }
        })

    return history

@interview_router.get("/roles")
async def get_available_roles():
    """Get list of available interview roles"""
    return {
        "roles": [
            "Data Scientist",
            "Machine Learning Engineer",
            "Data Analyst",
            "Data Engineer",
            "Quantitative Analyst",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "DevOps Engineer",
            "Software Engineer",
            "Product Manager",
            "Business Analyst",
            "Project Manager",
            "UX/UI Designer",
            "Cybersecurity Analyst",
            
        ]
    }