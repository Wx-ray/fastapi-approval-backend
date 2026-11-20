# 项目配置项：密钥、token 有效期、数据库地址
import os

# 生产环境应通过环境变量注入，这里先用本地开发默认值
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

DATABASE_URL = "sqlite:///./approval.db"
