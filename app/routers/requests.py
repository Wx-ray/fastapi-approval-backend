# 申请单：提交、查询台账、详情、编辑、删除、审批流转
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RequestModel
from app.schemas import RequestCreate, RequestUpdate, ReviewIn, RequestOut, PageOut
from app.dependencies import get_current_user, require_manager

router = APIRouter(prefix="/requests", tags=["申请单"])


def to_out(r: RequestModel) -> dict:
    # ORM 对象转成接口返回字典，关联申请人姓名一起带出
    return {
        "id": r.id,
        "title": r.title,
        "type": r.type,
        "reason": r.reason,
        "amount": r.amount,
        "start_date": r.start_date,
        "end_date": r.end_date,
        "status": r.status,
        "applicant_id": r.applicant_id,
        "applicant_name": r.applicant.username if r.applicant else "",
        "reviewer_id": r.reviewer_id,
        "review_note": r.review_note,
        "created_at": r.created_at,
        "reviewed_at": r.reviewed_at,
    }


def paginate(query, page: int, page_size: int) -> PageOut:
    total = query.count()
    rows = query.order_by(RequestModel.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageOut(total=total, page=page, page_size=page_size, items=[to_out(r) for r in rows])


def get_or_404(db: Session, request_id: int) -> RequestModel:
    row = db.query(RequestModel).filter(RequestModel.id == request_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请单不存在")
    return row


# ---------- 员工提交 ----------
@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = RequestModel(
        title=payload.title,
        type=payload.type,
        reason=payload.reason,
        amount=payload.amount,
        start_date=payload.start_date,
        end_date=payload.end_date,
        applicant_id=current.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_out(row)


# ---------- 我提交的 ----------
@router.get("/mine", response_model=PageOut)
def my_requests(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    query = db.query(RequestModel).filter(RequestModel.applicant_id == current.id)
    if status_filter:
        query = query.filter(RequestModel.status == status_filter)
    return paginate(query, page, page_size)


# ---------- 待我审批（审批人） ----------
@router.get("/pending", response_model=PageOut)
def pending_requests(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    query = db.query(RequestModel).filter(RequestModel.status == "pending")
    return paginate(query, page, page_size)


# ---------- 全部台账（审批人，可筛选） ----------
@router.get("", response_model=PageOut)
def ledger(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    type_filter: str | None = Query(None, alias="type"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    query = db.query(RequestModel)
    if status_filter:
        query = query.filter(RequestModel.status == status_filter)
    if type_filter:
        query = query.filter(RequestModel.type == type_filter)
    if keyword:
        query = query.filter(RequestModel.title.contains(keyword))
    return paginate(query, page, page_size)


# ---------- 详情 ----------
@router.get("/{request_id}", response_model=RequestOut)
def get_request(
    request_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_404(db, request_id)
    # 本人或审批人可看，其他人禁止
    if row.applicant_id != current.id and current.role != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该申请单")
    return to_out(row)


# ---------- 编辑（只能改自己待审批的单） ----------
@router.put("/{request_id}", response_model=RequestOut)
def update_request(
    request_id: int,
    payload: RequestUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_404(db, request_id)
    if row.applicant_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能修改自己提交的申请单")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已审批的申请单不能修改")

    if payload.title is not None:
        row.title = payload.title
    if payload.reason is not None:
        row.reason = payload.reason
    if payload.amount is not None:
        row.amount = payload.amount
    if payload.start_date is not None:
        row.start_date = payload.start_date
    if payload.end_date is not None:
        row.end_date = payload.end_date

    db.commit()
    db.refresh(row)
    return to_out(row)


# ---------- 删除（只能删自己待审批的单） ----------
@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_404(db, request_id)
    if row.applicant_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能删除自己提交的申请单")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已审批的申请单不能删除")

    db.delete(row)
    db.commit()


# ---------- 审批流转（审批人） ----------
@router.post("/{request_id}/review", response_model=RequestOut)
def review_request(
    request_id: int,
    payload: ReviewIn,
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    row = get_or_404(db, request_id)
    if row.applicant_id == manager.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能审批自己提交的申请单")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该申请单已审批，不能重复操作")

    row.status = "approved" if payload.action == "approve" else "rejected"
    row.reviewer_id = manager.id
    row.review_note = payload.note
    row.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(row)
    return to_out(row)
