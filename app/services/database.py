from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.entities import (
    Site, ChargerGroup, Pile, ChargingSession
)
from app.utils.logger import logger


class DatabaseService:
    def __init__(self):
        self.engine = create_async_engine(
            f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            pool_size=settings.DB_POOL_SIZE,
            pool_recycle=settings.DB_POOL_RECYCLE,
            echo=settings.DEBUG
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_db(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    # ... (之前实现的方法保持不变)

    async def get_site_statistics(self, site_no: str) -> Dict:
        """获取场站统计信息"""
        async with self.async_session() as session:
            try:
                # 获取场站基本信息
                site = await session.get(Site, site_no)
                if not site:
                    raise ValueError(f"场站不存在: {site_no}")

                # 获取充电桩数量
                pile_count = await session.scalar(
                    select(func.count(Pile.pile_sn))
                    .join(ChargerGroup)
                    .filter(ChargerGroup.site_no == site_no)
                )

                # 获取当前充电数量
                charging_count = await session.scalar(
                    select(func.count(ChargingSession.session_id))
                    .filter(
                        ChargingSession.site_no == site_no,
                        ChargingSession.status == 'CHARGING'
                    )
                )

                return {
                    "site_no": site_no,
                    "total_power_limit": site.total_power_limit,
                    "current_demand": site.demand,
                    "pile_count": pile_count,
                    "charging_count": charging_count,
                    "updated_at": datetime.utcnow()
                }

            except Exception as e:
                logger.error(f"获取场站统计信息失败: {str(e)}")
                raise

    async def cleanup_old_data(self):
        """清理过期数据"""
        async with self.async_session() as session:
            async with session.begin():
                try:
                    for table, days in settings.DATA_RETENTION.items():
                        cutoff_date = datetime.utcnow() - timedelta(days=days)
                        await session.execute(
                            text(f"DELETE FROM {table} WHERE created_at < :cutoff"),
                            {"cutoff": cutoff_date}
                        )
                    await session.commit()
                    logger.info("数据清理完成")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"数据清理失败: {str(e)}")
                    raise