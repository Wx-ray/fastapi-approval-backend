# 项目入口：创建 FastAPI 应用、建表、注册路由
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, requests

# 启动时按 ORM 模型建好数据表（已存在则跳过）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="内部审批台账后端", version="0.1.0")

app.include_router(auth.router)
app.include_router(requests.router)


@app.get("/")
def home():
    return {"项目": "内部审批台账后端", "接口文档": "/docs"}
