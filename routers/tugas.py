import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Task, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "static/uploads"


def save_attachment(upload_file: UploadFile | None, old_file: str | None = None):
    if not upload_file or not upload_file.filename:
        return None, None

    if old_file:
        old_path = os.path.join(UPLOAD_DIR, old_file)
        if os.path.exists(old_path):
            os.remove(old_path)

    file_extension = upload_file.filename.rsplit(".", 1)[-1] if "." in upload_file.filename else ""
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    contents = upload_file.file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return unique_filename, upload_file.filename


@router.get("/tasks/{user_id}", response_class=HTMLResponse)
def task_dashboard(
    user_id: int,
    request: Request,
    edit_task_id: int | None = None,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .all()
    )

    edit_task = None
    if edit_task_id:
        edit_task = (
            db.query(Task)
            .filter(Task.id == edit_task_id, Task.user_id == user_id)
            .first()
        )

    return templates.TemplateResponse(
        request,
        "tugas.html",
        {
            "user": user,
            "tasks": tasks,
            "edit_task": edit_task,
        },
    )


@router.get("/tasks/{user_id}/edit/{task_id}", response_class=HTMLResponse)
def edit_task_page(
    user_id: int,
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .all()
    )

    edit_task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )

    if not edit_task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    return templates.TemplateResponse(
        request,
        "tugas.html",
        {
            "user": user,
            "tasks": tasks,
            "edit_task": edit_task,
        },
    )


@router.post("/tasks/{user_id}/create")
async def create_task(
    user_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form("pending"),
    due_date: str = Form(""),
    is_completed: str = Form("off"),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    due_date_value = None
    if due_date:
        due_date_value = datetime.strptime(due_date, "%Y-%m-%d")

    attachment_file, attachment_name = save_attachment(file)

    new_task = Task(
        title=title,
        description=description,
        status=status,
        is_completed=is_completed == "on",
        due_date=due_date_value,
        attachment_file=attachment_file,
        attachment_name=attachment_name,
        user_id=user_id,
    )

    db.add(new_task)
    db.commit()

    return RedirectResponse(url=f"/tasks/{user_id}?created=1", status_code=303)


@router.post("/tasks/{user_id}/edit/{task_id}")
async def update_task(
    user_id: int,
    task_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form("pending"),
    due_date: str = Form(""),
    is_completed: str = Form("off"),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    task.title = title
    task.description = description
    task.status = status
    task.is_completed = is_completed == "on"

    if file and file.filename:
        attachment_file, attachment_name = save_attachment(file, task.attachment_file)
        task.attachment_file = attachment_file
        task.attachment_name = attachment_name

    if due_date:
        task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
    else:
        task.due_date = None

    db.commit()

    return RedirectResponse(url=f"/tasks/{user_id}?updated=1", status_code=303)


@router.post("/tasks/{user_id}/toggle/{task_id}")
def toggle_task(
    user_id: int,
    task_id: int,
    is_completed: str = Form("off"),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    task.is_completed = is_completed == "on"
    task.status = "completed" if task.is_completed else "pending"
    db.commit()

    return RedirectResponse(url=f"/tasks/{user_id}", status_code=303)


@router.post("/tasks/{user_id}/delete/{task_id}")
def delete_task(user_id: int, task_id: int, db: Session = Depends(get_db)):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    db.delete(task)
    db.commit()

    return RedirectResponse(url=f"/tasks/{user_id}?deleted=1", status_code=303)
