import json
import redis
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
from typing import Optional

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

redis_client = redis.asyncio.Redis(host="localhost", port=6379, decode_responses=True)

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
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = models.TaskModel(title=task.title, is_done=task.is_done)

    await db.add(db_task) 
    await db.commit() 
    await db.refresh(db_task)  

    return db_task


@app.get("/tasks", response_model=list[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    cached_tasks = await redis_client.get("all_tasks")

    if cached_tasks:
        print("Данные взяты из Redis")
        return json.loads(cached_tasks)

    print("Данные взяты из базы данных")

    tasks = db.query(models.TaskModel).all()
    tasks_jsonable = [TaskResponse.model_validate(task).model_dump() for task in tasks]
    await redis_client.set("all_tasks", json.dumps(tasks_jsonable), ex=60)

    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_one_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    db.delete(task)
    db.commit()

    await redis_client.delete("all_tasks")

    return {"message": "Задача удалена!"}


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача с таким id не найдена")

    update_data = task_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    await redis_client.delete("all_tasks")

    return task