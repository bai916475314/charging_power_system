from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.services.database import DatabaseService
from app.utils.logger import logger

router = APIRouter(prefix="/statistics", tags=["statistics"])

class StatisticsEndpoints:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    @router.get("/sites/{site_no}/power")
    async def get_site_power_statistics(
        self,
        site_no: str,
        period: str = "day"
    ) -> Dict:
        """获取场站功率统计"""
        try:
            end_time = datetime.utcnow()
            if period == "day":
                start_time = end_time - timedelta(days=1)
            elif period == "week":
                start_time = end_time - timedelta(days=7)
            elif period == "month":
                start_time = end_time - timedelta(days=30)
            else:
                raise HTTPException(status_code=400, detail="无效的时间周期")

            return await self.db_service.get_power_statistics(
                site_no,
                start_time,
                end_time
            )
        except Exception as e:
            logger.error(f"获取功率统计失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/sites/{site_no}/optimization")
    async def get_optimization_statistics(self, site_no: str) -> Dict:
        """获取优化效果统计"""
        try:
            return await self.db_service.get_optimization_statistics(site_no)
        except Exception as e:
            logger.error(f"获取优化统计失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))