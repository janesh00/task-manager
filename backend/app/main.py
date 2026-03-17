from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from pathlib import Path
import os
from .database import get_db, settings
from . import schemas, crud, auth, models

app = FastAPI(title="Task Manager API")

# Mount frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    try:
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    except Exception as e:
        print(f"Warning: Could not mount static files: {e}")

@app.get("/")
async def read_root():
    """Serve the frontend index.html for SPA routing"""
    index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Task Manager API - Frontend not found"}

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate,
    current_user = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_task(db=db, task=task, user_id=current_user.id)

@app.get("/tasks", response_model=List[schemas.Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    completed: bool = None,
    current_user = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_tasks(db, skip=skip, limit=limit, user_id=current_user.id, completed=completed)

@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int,
    current_user = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    current_user = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.update_task(db, task_id=task_id, task_update=task_update, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(
    task_id: int,
    current_user = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.delete_task(db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
