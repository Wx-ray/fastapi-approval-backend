# Pydantic 请求/响应模型：约束前端传什么、后端返回什么
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------- 认证 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    role: Literal["employee", "manager"] = "employee"


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- 申请单 ----------
class RequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    type: Literal["leave", "expense"]
    reason: str
    amount: float = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class RequestUpdate(BaseModel):
    title: Optional[str] = None
    reason: Optional[str] = None
    amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReviewIn(BaseModel):
    action: Literal["approve", "reject"]
    note: Optional[str] = None


class RequestOut(BaseModel):
    id: int
    title: str
    type: str
    reason: str
    amount: float
    start_date: Optional[str]
    end_date: Optional[str]
    status: str
    applicant_id: int
    applicant_name: str
    reviewer_id: Optional[int]
    review_note: Optional[str]
    created_at: Optional[datetime]
    reviewed_at: Optional[datetime]


class PageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RequestOut]
