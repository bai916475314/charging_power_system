from functools import lru_cache
from typing import Dict, List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 基础配置
    PROJECT_NAME: str = "充电桩功率调度系统"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "charging_system"
    DB_POOL_SIZE: int = 20
    DB_POOL_RECYCLE: int = 3600

    # Kafka配置
    KAFKA_SERVERS: List[str] = ["localhost:9092"]
    KAFKA_GROUP_ID: str = "charging_group"
    KAFKA_TOPICS: Dict[str, str] = {
        "VEHICLE_RECOGNITION": "vehicle_recognition",
        "POWER_PREDICTION": "power_prediction",
        "PLUG_STATUS": "plug_status",
        "POWER_ALLOCATION": "power_allocation"
    }

    # 运维平台配置
    MAINTENANCE_API_URL: str = "http://maintenance-api"
    MAINTENANCE_API_TIMEOUT: int = 30

    # 数据保留配置
    DATA_RETENTION: Dict[str, int] = {
        "charging_record": 90,  # 90天
        "optimization_task": 30,  # 30天
        "power_prediction": 7  # 7天
    }

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 算法配置
    MAX_POWER_REDUCTION: float = 0.3  # 最大功率下调30%
    MIN_POWER_IMPACT: float = 0.1  # 10%以下不计入影响

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()