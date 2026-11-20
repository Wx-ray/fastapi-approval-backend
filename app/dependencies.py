# 公共依赖：从 token 解析当前登录用户、校验审批人角色
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# tokenUrl 只用于 Swagger 文档里标出登录接口，不影响实际鉴权
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证无效或已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exc
    return user


def require_manager(current: User = Depends(get_current_user)) -> User:
    if current.role != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅审批人可执行此操作")
    return current
