import json
from typing import List
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, HTTPException,Request
import google.generativeai as genai
from requests import Session

from src.db.db import get_db
from src.db.models import Quiz
from src.schemas.quiz import QuizResponse, QuizCreate
from src.schemas.quiz import QuizResult
from src.db.models import User, QuizAttempt
from src.schemas.quiz import QuestionOption, Question, QuizSubmission
from src.services.auth_service import get_current_user
from fastapi import status
from src.services.auth_service import decode_token

QUIZ_PROMPT_TEMPLATE = """
Create a quiz for the subject: {subject} with {num_questions} questions.
Each question should have 4 options.
The response should be in the following JSON format:
{{
    "questions": [
        {{
            "text": "question text",
            "options": [
                {{"text": "option text", "is_correct": true/false}},
                ...
            ],
            "multiple_correct": true/false
        }},
        ...
    ]
}}
Make sure some questions have multiple correct answers (set multiple_correct to true).
The questions should test understanding and not just memorization.
"""

quiz_router = APIRouter(prefix="/quiz", tags=["quiz"])

# Initialize Gemini Pro
genai.configure(api_key='AIzaSyCuDaMhFlW1C_-MZAbyOQ6XFpfVS2plSfk')
model = genai.GenerativeModel('gemini-1.5-flash')


def generate_uuid_for_json(quiz_json: dict) -> dict:
    """Replace placeholder UUIDs with actual UUIDs in the quiz JSON"""
    for question in quiz_json["questions"]:
        question["id"] = str(uuid4())
        for option in question["options"]:
            option["id"] = str(uuid4())
    return quiz_json


@quiz_router.post("/generate", response_model=QuizResponse)
async def generate_quiz(quiz_data: QuizCreate, db: Session = Depends(get_db)):
    prompt = QUIZ_PROMPT_TEMPLATE.format(
        subject=quiz_data.subject,
        num_questions=quiz_data.num_questions
    )

    try:
        response = model.generate_content(prompt)
        content_text = response.text.strip()

        # Clean up the JSON string
        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.endswith("```"):
            content_text = content_text[:-3]
        content_text = content_text.strip()

        # Parse the JSON response
        quiz_json = json.loads(content_text)

        # Generate UUIDs for questions and options
        questions_with_ids = []
        for question in quiz_json["questions"]:
            question_id = str(uuid4())
            options_with_ids = []

            for option in question["options"]:
                option_with_id = {
                    "id": str(uuid4()),
                    "text": option["text"],
                    "is_correct": option["is_correct"]
                }
                options_with_ids.append(option_with_id)

            question_with_id = {
                "id": question_id,
                "text": question["text"],
                "options": options_with_ids,
                "multiple_correct": question["multiple_correct"]
            }
            questions_with_ids.append(question_with_id)

        # Create the database entry with the UUID-enhanced questions
        db_quiz = Quiz(
            subject=quiz_data.subject,
            questions=questions_with_ids  # Store the questions with UUIDs
        )
        db.add(db_quiz)
        db.commit()
        db.refresh(db_quiz)

        # Create the response object
        return QuizResponse(
            id=db_quiz.id,
            subject=db_quiz.subject,
            questions=[
                Question(
                    id=UUID(q["id"]),
                    text=q["text"],
                    options=[
                        QuestionOption(
                            id=UUID(opt["id"]),
                            text=opt["text"],
                            is_correct=opt["is_correct"]
                        ) for opt in q["options"]
                    ],
                    multiple_correct=q["multiple_correct"]
                ) for q in db_quiz.questions
            ],
            created_at=db_quiz.created_at
        )
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
        )


@quiz_router.post("/submit", response_model=QuizResult)
async def submit_quiz(
        request: Request,
        submission: QuizSubmission,
        db: Session = Depends(get_db),
):
    # Authentication check
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    email = decode_token(access_token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    print("Debug: Quiz ID:", quiz.id)
    print("Debug: Quiz questions type:", type(quiz.questions))
    print("Debug: Quiz questions:", quiz.questions)
    print("Debug: Submission answers:", submission.answers)

    correct_answers = 0
    feedback = []
    total_questions = len(quiz.questions)

    # Create a dictionary of questions for easier lookup
    questions_dict = {}
    for q in quiz.questions:
        # Handle both string and dict cases
        if isinstance(q, dict):
            q_id = q.get('id')
        else:
            q_id = q.id
        questions_dict[str(q_id)] = q

    print("Debug: Questions dictionary:", questions_dict)

    # Process each submitted answer
    for answer in submission.answers:
        question_id_str = str(answer.question_id)
        print(f"\nProcessing answer for question {question_id_str}")

        # Find the matching question
        question = questions_dict.get(question_id_str)
        if not question:
            print(f"Question {question_id_str} not found in quiz")
            continue

        print(f"Found matching question: {question}")

        # Extract options based on question structure
        if isinstance(question, dict):
            options = question.get('options', [])
            multiple_correct = question.get('multiple_correct', False)
        else:
            options = question.options
            multiple_correct = question.multiple_correct

        # Get correct options for this question
        correct_option_ids = set()
        for opt in options:
            if isinstance(opt, dict):
                if opt.get('is_correct', False):
                    correct_option_ids.add(str(opt['id']))
            else:
                if opt.is_correct:
                    correct_option_ids.add(str(opt.id))

        # Get selected options
        selected_option_ids = {str(opt_id) for opt_id in answer.selected_option_ids}

        print(f"Debug: Correct options: {correct_option_ids}")
        print(f"Debug: Selected options: {selected_option_ids}")
        print(f"Debug: Multiple correct: {multiple_correct}")

        # Determine if answer is correct
        is_correct = False
        if multiple_correct:
            is_correct = correct_option_ids == selected_option_ids
        else:
            is_correct = (len(selected_option_ids) == 1 and
                          len(correct_option_ids.intersection(selected_option_ids)) == 1)

        print(f"Debug: Is answer correct? {is_correct}")

        if is_correct:
            correct_answers += 1
            feedback.append(f"Question {question_id_str}: Correct!")
        else:
            feedback.append(f"Question {question_id_str}: Incorrect")

    # Calculate score
    print(f"\nFinal scoring:")
    print(f"Correct answers: {correct_answers}")
    print(f"Total questions: {total_questions}")

    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    print(f"Score percentage: {score_percentage}")

    # Create serialized answers
    serialized_answers = [
        {
            "question_id": str(answer.question_id),
            "selected_option_ids": [str(opt_id) for opt_id in answer.selected_option_ids]
        }
        for answer in submission.answers
    ]

    # Create quiz attempt
    quiz_attempt = QuizAttempt(
        id=uuid4(),
        quiz_id=submission.quiz_id,
        user_id=user.id,
        answers=serialized_answers,
        score=score_percentage
    )

    db.add(quiz_attempt)
    db.commit()
    db.refresh(quiz_attempt)

    return QuizResult(
        id=quiz_attempt.id,
        quiz_id=quiz_attempt.quiz_id,
        user_id=quiz_attempt.user_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score_percentage=score_percentage,
        feedback=feedback,
        created_at=quiz_attempt.created_at
    )


@quiz_router.get("/history", response_model=List[QuizResult])
async def get_quiz_history(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.created_at.desc()).all()

    results = []
    for attempt in attempts:
        quiz = db.query(Quiz).get(attempt.quiz_id)
        if quiz:
            results.append(QuizResult(
                id=attempt.id,
                quiz_id=attempt.quiz_id,
                user_id=attempt.user_id,
                total_questions=len(quiz.questions),
                correct_answers=int((attempt.score / 100) * len(quiz.questions)),
                score_percentage=attempt.score,
                feedback=[],  # Historical feedback not stored
                created_at=attempt.created_at
            ))

    return results


@quiz_router.get("/retry/{quiz_id}", response_model=QuizResponse)
async def retry_quiz(quiz_id: UUID, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return QuizResponse(
        id=quiz.id,
        subject=quiz.subject,
        questions=[
            Question(
                id=UUID(q["id"]),
                text=q["text"],
                options=[
                    QuestionOption(
                        id=UUID(opt["id"]),
                        text=opt["text"],
                        is_correct=opt["is_correct"]
                    ) for opt in q["options"]
                ],
                multiple_correct=q["multiple_correct"]
            ) for q in quiz.questions
        ],
        created_at=quiz.created_at
    )