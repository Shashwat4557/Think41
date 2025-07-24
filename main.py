from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from enum import Enum

app = FastAPI()

DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_str_id = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    estimated_time_minutes = Column(Integer)
    status = Column(String, default=TaskStatus.pending)
    submitted_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class TaskCreate(BaseModel):
    task_str_id: str = Field(..., alias="task_strId")
    description: str
    estimated_time_minutes: int = Field(..., gt=0)

class StatusUpdate(BaseModel):
    new_status: TaskStatus

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/tasks")
def create_task(task: TaskCreate):
    db = SessionLocal()
    existing_task = db.query(Task).filter(Task.task_str_id == task.task_str_id).first()
    if existing_task:
        raise HTTPException(status_code=400, detail="task_strId must be unique")
    db_task = Task(
        task_str_id=task.task_str_id,
        description=task.description,
        estimated_time_minutes=task.estimated_time_minutes,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {
        "internal_db_id": db_task.id,
        "task_strId": db_task.task_str_id,
        "status": db_task.status,
    }

@app.get("/tasks/{task_str_id}")
def get_task(task_str_id: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_str_id == task_str_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_str_id}/status")
def update_status(task_str_id: str, status_update: StatusUpdate):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_str_id == task_str_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Prevent status regression
    current_status = task.status
    new_status = status_update.new_status
    valid_transitions = {
        "pending": ["processing", "completed"],
        "processing": ["completed"],
        "completed": [],
    }
    if new_status not in valid_transitions[current_status]:
        raise HTTPException(status_code=400, detail=f"Invalid status transition from {current_status} to {new_status}")

    task.status = new_status
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/next-to-process")
def get_next_task():
    db = SessionLocal()
    task = (
        db.query(Task)
        .filter(Task.status == "pending")
        .order_by(Task.estimated_time_minutes.asc(), Task.submitted_at.asc())
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="No pending tasks found")
    return task

@app.get("/tasks/pending")
def list_pending_tasks(
    sort_by: Optional[str] = Query("estimated_time_minutes", pattern="^(estimated_time_minutes|submitted_at)$"),
    order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    limit: Optional[int] = Query(None, gt=0),
):
    db = SessionLocal()
    query = db.query(Task).filter(Task.status == "pending")

    sort_column = Task.estimated_time_minutes if sort_by == "estimated_time_minutes" else Task.submitted_at
    sort_column = sort_column.asc() if order == "asc" else sort_column.desc()

    tasks = query.order_by(sort_column)
    if limit:
        tasks = tasks.limit(limit)
    return tasks.all()
