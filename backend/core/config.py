import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Timeline Project APIs"
    API_V1_STR: str = "/api"
    
    # 存储目录配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
    DELETED_DIR: str = os.getenv("DELETED_DIR", os.path.join(BASE_DIR, "deleted"))

    # 管理员密码配置
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "123456")

settings = Settings()

# 确保启动时目录存在
for directory in [settings.UPLOAD_DIR, settings.DATA_DIR, settings.DELETED_DIR]:
    os.makedirs(directory, exist_ok=True)
