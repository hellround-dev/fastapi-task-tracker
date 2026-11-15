from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
from typing import Optional

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    title: str
    is_done: bool = False


class TaskResponse(TaskCreate):
    id: int

    class Config:
        from_attributes = True  


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = models.TaskModel(title=task.title, is_done=task.is_done)

    db.add(db_task) 
    db.commit() 
    db.refresh(db_task)  

    return db_task


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(models.TaskModel).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_one_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    return task


@app.delete("/tasks/{task_id}")
def get_one_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    db.delete(task)
    db.commit()
    return {"message": "Задача удалена!"}


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    update_data = task_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task