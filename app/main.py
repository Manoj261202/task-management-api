from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Path, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from . import models, schemas, crud, auth, database, email_utils
from app.celery_worker import send_email_async

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Task Manager API - MacV AI")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Login request schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# AUTH
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@app.post("/login", response_model=schemas.TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token(sub=user.email)
    return {"access_token": token, "token_type": "bearer"}

# PROJECTS
@app.post("/projects", response_model=schemas.ProjectOut)
def create_project(project: schemas.ProjectCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return crud.create_project(db, project, current_user.id)

@app.get("/projects", response_model=list[schemas.ProjectOut])
def get_projects(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return crud.get_user_projects(db, current_user.id)

@app.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project_details(
    project_id: int = Path(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")
    return project

@app.patch("/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, project: schemas.ProjectCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    updated_project = crud.update_project(db, project_id, current_user.id, project)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")
    return updated_project

@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    success = crud.delete_project(db, project_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")
    return None

# TASKS
@app.post("/tasks", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    project = crud.get_project(db, task.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Project not found or not owned by current user")
    created_task = crud.create_task(db, task)
    if task.assigned_user_id:
        assigned = crud.get_user_by_id(db, task.assigned_user_id)
        if assigned:
            send_email_async.delay(assigned.email, "Task Assigned", f"You have been assigned task: {task.title}")
    return created_task

@app.get("/tasks", response_model=list[schemas.TaskOut])
def get_tasks(status: str = None, priority: int = None, project_id: int = None, due_date: str = None,
              skip: int = 0, limit: int = 10,
              current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    tasks = crud.get_tasks_filtered(db, current_user.id, skip=skip, limit=limit, status=status,
                                    priority=priority, project_id=project_id, due_date=due_date)
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task_details(
    task_id: int = Path(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.get_task_with_owner(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not owned by user")
    return task

@app.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, task_update: schemas.TaskCreate, background_tasks: BackgroundTasks, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = crud.get_project(db, db_task.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to update task")

    old_assigned_user_id = db_task.assigned_user_id
    old_status = db_task.status

    # Update fields
    db_task.title = task_update.title
    db_task.description = task_update.description
    db_task.status = task_update.status
    db_task.priority = task_update.priority
    db_task.due_date = task_update.due_date
    db_task.assigned_user_id = task_update.assigned_user_id

    db.commit()
    db.refresh(db_task)

    if task_update.assigned_user_id and task_update.assigned_user_id != old_assigned_user_id:
        assigned_user = crud.get_user_by_id(db, task_update.assigned_user_id)
        if assigned_user:
            send_email_async.delay(assigned_user.email, "Task Assigned", f"You have been assigned task: {db_task.title}")
    elif old_status != task_update.status:
        assigned_user = crud.get_user_by_id(db, db_task.assigned_user_id)
        if assigned_user:
            email_utils.send_email_background(background_tasks, assigned_user.email, "Task Status Updated", f"Status of task '{db_task.title}' changed to {db_task.status}")

    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    project = crud.get_project(db, db_task.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to delete task")
    db.delete(db_task)
    db.commit()
    return None
