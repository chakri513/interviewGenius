import os
import json
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Form, UploadFile, Depends, HTTPException, File, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from src.db.db import get_db
from src.db.models import Submission, SubmissionFile, Comment, User
from src.schemas.submission import (
    SubmissionResponse,
    SubmissionType,
    CommentResponse,
    CommentCreate,
    SubmissionCreate,
    UpdateSubmission,
    SubmissionCreateWithCourse,
    SubmissionResponseWithCourse,
)
from src.services.auth_service import get_current_user, decode_token
from starlette import status
from pathlib import Path
from src.schemas.submission import FileResponse
submission_router = APIRouter(prefix="/submissions", tags=["submissions"])

@submission_router.get("/", response_model=List[SubmissionResponse])
async def list_submissions(request: Request, db: Session = Depends(get_db)):
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
    submissions = db.query(Submission).order_by(Submission.created_at.desc()).all()
    return submissions

@submission_router.post("/", response_model=SubmissionResponseWithCourse)
async def create_submission(
    request: Request,
    submission: str = Form(...),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> SubmissionResponseWithCourse:
    try:
        submission_data = SubmissionCreateWithCourse(**json.loads(submission))
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


        submission_db = Submission(
            title=submission_data.title,
            type=submission_data.type,
            description=submission_data.description,
            user_id=user.id,
            course_name=submission_data.course_name,
            course_id=submission_data.course_id,
            dept=submission_data.dept,
            due_date=submission_data.due_date,
        )



        db.add(submission_db)
        db.flush()

        submission_files = await process_and_save_files(
            files=files, submission_db=submission_db, user=user, db=db
        )

        db.commit()
        db.refresh(submission_db)


        return SubmissionResponseWithCourse.from_orm(submission_db)



    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submission data format",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {e}"
        )

@submission_router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    request: Request,
    submission_id: UUID,
    submission_data: str = Form(...),
    new_files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Update an existing submission, including its files."""
    try:
        update_data = UpdateSubmission(**json.loads(submission_data))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submission data format",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    # Validate authentication
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

    submission_db = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Update basic submission fields if provided
    if update_data.title is not None:
        submission_db.title = update_data.title
    if update_data.type is not None:
        submission_db.type = update_data.type
    if update_data.description is not None:
        submission_db.description = update_data.description

    submission_files = await process_and_save_files(
        files=new_files, submission_db=submission_db, user=user, db=db, delete_existing=True
    )

    db.commit()
    db.refresh(submission_db)

    return SubmissionResponse(
        id=submission_db.id,
        type=submission_db.type,
        title=submission_db.title,
        description=submission_db.description,
        created_at=submission_db.created_at,
        user_id=submission_db.user_id,
        files=submission_files,
    )

@submission_router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(request: Request,
    submission_id: int,
    db: Session = Depends(get_db),

):
    """Get a specific submission with file details."""
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    else:
        email = decode_token(access_token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Fetch associated files
    files = db.query(SubmissionFile).filter(SubmissionFile.submission_id == submission_id).all()
    file_responses = [
        FileResponse(
            filename=f.filename, file_path=f.file_path, file_type=f.file_type
        )
        for f in files
    ]

    return SubmissionResponse(
        id=submission.id,
        type=submission.type,
        title=submission.title,
        description=submission.description,
        created_at=submission.created_at,
        user_id=submission.user_id,
        files=file_responses,
    )

@submission_router.post("/{submission_id}/comments", response_model=CommentResponse)
async def create_comment(
    submission_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    db_comment = Comment(
        content=comment.content,
        submission_id=submission_id,
        user_id=current_user.id,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@submission_router.get("/{submission_id}/comments", response_model=List[CommentResponse])
async def get_submission_comments(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comments = db.query(Comment).filter(Comment.submission_id == submission_id).all()
    return comments

async def process_and_save_files(
    files: Optional[List[UploadFile]],
    submission_db: Submission,
    user: User,
    db: Session,
    delete_existing: bool = False,
) -> List[FileResponse]:
    """Processes and saves uploaded files, handling directory creation."""
    submission_files = []
    if delete_existing:
        existing_files = db.query(SubmissionFile).filter(SubmissionFile.submission_id == submission_db.id).all()
        for existing_file in existing_files:
            file_path = Path(existing_file.file_path)
            if file_path.exists():
                os.remove(file_path)
            db.delete(existing_file)
        db.flush()

    if files:
        for file in files:
            if file.filename and file.size > 0:
                safe_filename = f"{user.username}_{file.filename}"
                base_folder = submission_db.type.value
                file_location = f"uploads/{base_folder}/{submission_db.id}/{safe_filename}"

                os.makedirs(os.path.dirname(file_location), exist_ok=True)

                try:
                    with open(file_location, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)

                    submission_file = SubmissionFile(
                        filename=file.filename,
                        file_path=file_location,
                        file_type=file.content_type,
                        submission_id=submission_db.id,
                    )
                    db.add(submission_file)
                    submission_files.append(
                        FileResponse(
                            filename=file.filename,
                            file_path=file_location,
                            file_type=file.content_type,
                        )
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Could not save file {file.filename}: {e}",
                    )
    return submission_files

async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to the specified destination."""
    dest_path = Path(destination)
    os.makedirs(dest_path.parent, exist_ok=True)
    try:
        with open(dest_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)

        if not os.path.exists(dest_path):
            raise IOError("Failed to save file")

        return str(dest_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save file: {str(e)}"
        )