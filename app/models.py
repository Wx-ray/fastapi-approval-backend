# ORM 表模型：用户表、申请单表
from datetime import datetime
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # employee 普通员工 / manager 审批人
    role: Mapped[str] = mapped_column(String(20), default="employee")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    requests = relationship("RequestModel", back_populates="applicant", foreign_keys="RequestModel.applicant_id")


class RequestModel(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))
    # leave 请假 / expense 报销
    type: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Float, default=0)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # pending 待审批 / approved 已通过 / rejected 已驳回
    status: Mapped[str] = mapped_column(String(20), default="pending")

    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    applicant = relationship("User", back_populates="requests", foreign_keys=[applicant_id])
