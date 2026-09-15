# 配置文件：从环境变量中去加载配置信息, 并提供给其他模块使用
import os
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    ######## LLM 配置 ########
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL_NAME: str
    DEEPSEEK_REASONING_EFFORT: str = "high"         # 模型推理强度
    DEEPSEEK_API_TIMEOUT: float = 60.0              # 模型请求超时时间


    ######## 服务器配置 ########
    SERVER_HOST: str
    SERVER_PORT: int  


    ######## 数据库配置 ########
    # 数据库类型
    DATABASE_TYPE: str = "mysql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    # 数据库连接池
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_POOL_RECYCLE: int


    ######## JWT 配置 ########
    SECRET_KEY: str                     # 密钥
    JWT_ALGORITHM: str = "HS256"        # 加密方式
    JWT_EXPIRE_DAYS: int = 7            # JWT 过期时间


    ######## RAG 配置 ########
    DIMENSION: int              # 向量维度
    CHUNK_SIZE: int             # 切割后的文本块大小
    CHUNK_OVERLAP: int          # 块重叠数量
    RAG_DOC_PATH: str           # RAG 源文档路径


    # 加载环境变量(优先会从系统环境变量中加载, 如果没有, 则从.env文件中加载, 如果也没有, 则使用默认值)
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), "..", ".env"), env_file_encoding="utf-8")
    

    # 数据库连接URL
    def get_database_url(self) -> str:
        return f"{self.DATABASE_TYPE}+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

# 单例
settings = get_settings()