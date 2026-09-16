from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from packages.core.config import settings




# 数据库引擎
engine = create_engine(
    url = settings.get_database_url(),
    pool_size = settings.DATABASE_POOL_SIZE,
    max_overflow = settings.DATABASE_MAX_OVERFLOW,
    pool_recycle = settings.DATABASE_POOL_RECYCLE
)

# 会话工厂
session_factory = sessionmaker(
    bind = engine,            # 绑定
    autoflush = True,         # 自动刷新
)

# 数据库元数据
Base = declarative_base()

# 创建会话依赖的方法
def get_db():
    # 创建一个会话
    session = session_factory()
    try:
        yield session
    finally:
        # 关闭会话
        session.close()