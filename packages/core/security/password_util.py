# 密码工具：使用 bcrypt 做单向哈希与校验
import bcrypt


def hash_password(plain_password: str) -> str:
    """
    对明文密码做 bcrypt 哈希。
    :param plain_password: 明文密码
    :return: 60 字符的哈希串，可直接存入数据库
    """
    if not plain_password:
        raise ValueError("密码不能为空")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")




def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码与数据库中的哈希是否匹配。
    :param plain_password: 用户输入的明文密码
    :param hashed_password: 数据库中存储的哈希串
    :return: True 表示匹配，False 表示不匹配
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # 哈希串格式错误时直接返回 False，不抛异常
        return False