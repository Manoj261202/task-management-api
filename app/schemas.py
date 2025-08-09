from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = Field(default="pending")
    priority: Optional[int] = Field(default=0)
    due_date: Optional[date] = None

class TaskCreate(TaskBase):
    project_id: int
    assigned_user_id: Optional[int] = None

class TaskOut(TaskBase):
    id: int
    project_id: int
    assigned_user_id: Optional[int] = None
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    tasks: List[TaskOut] = []
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
