# 密码哈希校验、JWT 令牌生成与解析
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    # bcrypt 自动加盐，返回可直接存库的哈希字符串
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    # 过期或伪造会抛 JWTError，由调用方捕获转成 401
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
