import time
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from .database import SessionLocal, engine
from . import models, schemas, crud

app = FastAPI(title="ToDo DevOps API")


# === Database connection with retry (Docker-safe) ===
for i in range(10):
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database connected")
        break
    except OperationalError:
        print("Waiting for database...")
        time.sleep(2)
else:
    raise RuntimeError("Database connection failed")


# === Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === Health check ===
@app.get("/health")
def health():
    return {"status": "ok"}


# === Create task ===
@app.post("/tasks", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db)
):
    return crud.create_task(db, task)


# === Read tasks ===
@app.get("/tasks", response_model=list[schemas.TaskResponse])
def read_tasks(db: Session = Depends(get_db)):
    return crud.get_tasks(db)


# === Update task ===
@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    completed: bool,
    db: Session = Depends(get_db)
):
    task = crud.update_task(db, task_id, completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "updated"}


# === Delete task ===
@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = crud.delete_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "deleted"}
