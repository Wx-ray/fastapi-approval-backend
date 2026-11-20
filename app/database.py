# 数据库引擎、会话工厂和 ORM 基类
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL

# SQLite 专用参数：允许多线程共用连接
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# 每个请求拿一个数据库会话，用完关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
