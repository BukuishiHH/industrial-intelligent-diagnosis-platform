from sqlalchemy.orm import Session
from packages.db.user import User
from typing import Optional


class UserDao:

    # 根据用户名获取用户信息
    def get_username(self, username: str, db: Session) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    # 创建用户
    def create_user(self, username: str, password: str, db:Session) -> Optional[User]:
        user = User(
            username = username,
            password = password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
        

# 创建单例对象
user_dao = UserDao()