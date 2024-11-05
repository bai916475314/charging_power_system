import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.endpoints import HTTPService
from app.core.config import settings
from app.services.algorithm import AlgorithmService
from app.services.database import DatabaseService
from app.services.kafka import KafkaService
from app.utils.logger import logger

# 创建FastAPI应用实例
app = FastAPI(
    title="充电桩功率调度系统",
    description="基于FastAPI的充电桩功率调度系统",
    version="1.0.0"
)


# CORS和异常处理配置保持不变...

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        # 初始化服务
        logger.info("正在初始化服务组件...")

        # 初始化数据库服务
        db_service = DatabaseService()
        await db_service.initialize()

        # 初始化算法和Kafka服务
        algorithm_service = AlgorithmService(db_service, None)
        kafka_service = KafkaService(algorithm_service)
        algorithm_service.kafka_service = kafka_service

        # 初始化HTTP服务
        http_service = HTTPService(db_service, algorithm_service)

        # 注册服务
        app.state.db = db_service
        app.state.kafka = kafka_service
        app.state.algorithm = algorithm_service
        app.state.http = http_service

        # 启动Kafka消费者
        kafka_consumer_task = asyncio.create_task(
            kafka_service.start_consuming()
        )

        logger.info("所有服务组件初始化完成")
        yield

        # 清理资源
        logger.info("正在关闭服务...")
        kafka_consumer_task.cancel()
        await kafka_service.close()
        await db_service.close()
        logger.info("所有服务已安全关闭")

    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise


# 路由和状态检查接口保持不变...

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=settings.WORKERS
    )