import uvicorn
from fastapi import FastAPI
from packages.core.config import settings
from packages.core.database import Base, engine

# 自动建表
Base.metadata.create_all(bind=engine)


app = FastAPI()


# 注册路由
# app.include_router()


if __name__=="__main__":
    uvicorn.run(
        "apps.api.main:app",
        host = settings.SERVER_HOST,
        port = settings.SERVER_PORT,
        reload=True,
                )