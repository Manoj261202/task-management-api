from sqlalchemy.orm import Session
from . import models, schemas
from passlib.hash import bcrypt
from sqlalchemy import and_

def create_user(db: Session, user: schemas.UserCreate):
    hashed = bcrypt.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_project(db: Session, project: schemas.ProjectCreate, owner_id: int):
    db_project = models.Project(name=project.name, description=project.description, owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_user_projects(db: Session, owner_id: int):
    return db.query(models.Project).filter(models.Project.owner_id == owner_id).all()

def get_project(db: Session, project_id: int, owner_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == owner_id).first()

def update_project(db: Session, project_id: int, owner_id: int, project_update: schemas.ProjectCreate):
    project = get_project(db, project_id, owner_id)
    if not project:
        return None
    project.name = project_update.name
    project.description = project_update.description
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project_id: int, owner_id: int):
    project = get_project(db, project_id, owner_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        project_id=task.project_id,
        assigned_user_id=task.assigned_user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks_filtered(db: Session, skip: int = 0, limit: int = 10, status=None, priority=None, project_id=None, due_date=None, sort_by=None, sort_order="asc"):
    q = db.query(models.Task)
    if status:
        q = q.filter(models.Task.status == status)
    if priority is not None:
        q = q.filter(models.Task.priority == priority)
    if project_id:
        q = q.filter(models.Task.project_id == project_id)
    if due_date:
        q = q.filter(models.Task.due_date == due_date)
    
    if sort_by in ["priority", "due_date"]:
        col = getattr(models.Task, sort_by)
        if sort_order == "desc":
            col = col.desc()
        q = q.order_by(col)
    return q.offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_task_with_owner(db: Session, task_id: int, owner_id: int):
    return db.query(models.Task).join(models.Project).filter(
        models.Task.id == task_id,
        models.Project.owner_id == owner_id
    ).first()

def update_task(db: Session, task_id: int, task_update: schemas.TaskCreate):
    task = get_task(db, task_id)
    if not task:
        return None
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: int):
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True


def get_tasks_filtered(db: Session, user_id: int, skip: int = 0, limit: int = 10, status=None, priority=None, project_id=None, due_date=None):
    q = db.query(models.Task).join(models.Project).filter(models.Project.owner_id == user_id)
    if status:
        q = q.filter(models.Task.status == status)
    if priority is not None:
        q = q.filter(models.Task.priority == priority)
    if project_id:
        q = q.filter(models.Task.project_id == project_id)
    if due_date:
        q = q.filter(models.Task.due_date == due_date)
    return q.offset(skip).limit(limit).all()