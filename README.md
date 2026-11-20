# 内部审批台账后端（FastAPI）

一个面向企业内部的简化 OA 后端：员工提交请假 / 报销申请，审批人在线通过或驳回，所有单据进入台账，支持按类型、状态、关键词检索与分页。

## 技术栈

- Python 3.11 + FastAPI
- SQLAlchemy 2.0（ORM）+ SQLite（零安装，可平滑切换 PostgreSQL）
- JWT（python-jose）登录鉴权，bcrypt 密码哈希
- Pydantic v2 请求 / 响应模型校验

## 目录结构

```
backend/
├── app/
│   ├── main.py            # 入口：建表、注册路由
│   ├── config.py          # 配置项（密钥、token 有效期、数据库地址）
│   ├── database.py        # 引擎、会话工厂、ORM 基类、get_db 依赖
│   ├── security.py        # 密码哈希、JWT 生成 / 解析
│   ├── models.py          # ORM 模型：User、RequestModel
│   ├── schemas.py         # Pydantic 请求 / 响应模型
│   ├── dependencies.py    # 公共依赖：当前登录用户、审批人校验
│   └── routers/
│       ├── auth.py        # 注册、登录
│       └── requests.py    # 申请单 CRUD、筛选分页、审批流转
├── requirements.txt
└── .gitignore
```

## 启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（工作目录在 backend/ 下）
uvicorn app.main:app --port 8001 --reload
```

启动后访问：

- Swagger 接口文档：http://127.0.0.1:8001/docs
- 根路径：http://127.0.0.1:8001/

## 业务与权限规则

- 角色：`employee` 普通员工、`manager` 审批人。
- 员工：提交申请、查看 / 编辑 / 删除自己提交的单据；只有 `pending`（待审批）状态的单据才能改、能删。
- 审批人：查看全部台账、待办列表，对单据通过（`approved`）或驳回（`rejected`）；不能审批自己提交的单据。
- 单据类型：`leave` 请假、`expense` 报销；状态：`pending` 待审批、`approved` 已通过、`rejected` 已驳回。

## 接口清单

### 认证

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/auth/register` | 注册（可指定 role，默认 employee） | 无 |
| POST | `/auth/login` | 登录，返回 access_token 与用户信息 | 无 |

### 申请单

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/requests` | 提交申请单 | 登录 |
| GET | `/requests/mine` | 我提交的（可按 status 筛选，分页） | 登录 |
| GET | `/requests/pending` | 待我审批（分页） | 审批人 |
| GET | `/requests` | 全部台账（status / type / keyword 筛选，分页） | 审批人 |
| GET | `/requests/{id}` | 单据详情（本人或审批人） | 登录 |
| PUT | `/requests/{id}` | 编辑自己的待审批单 | 登录 |
| DELETE | `/requests/{id}` | 删除自己的待审批单 | 登录 |
| POST | `/requests/{id}/review` | 审批：approve / reject，可填备注 | 审批人 |

分页参数：`page`（默认 1）、`page_size`（默认 10，最大 50）；返回 `total / page / page_size / items`。

## 演示流程

1. `POST /auth/register` 注册一个 `manager` 账号和一个 `employee` 账号，各自登录拿 token。
2. 员工登录后 `POST /requests` 提交一张请假单、一张报销单。
3. 审批人登录后 `GET /requests/pending` 看待办，`POST /requests/{id}/review` 分别通过、驳回。
4. 审批人 `GET /requests?status=approved&type=leave&keyword=请假` 验证组合筛选与分页。

## 可扩展方向

- 接入 PostgreSQL，补 Alembic 数据库迁移。
- 增加审批层级（多级审批）、评论 / 附件、操作日志。
- 台账导出 Excel、按时间区间统计审批通过率。
- 接口补充单元测试（pytest + TestClient）。
