from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from packages.core.database import Base

class User(Base):
    # 表名
    __tablename__ = "users"
    # 字段
    userid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户id")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="用户名称")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="用户密码")