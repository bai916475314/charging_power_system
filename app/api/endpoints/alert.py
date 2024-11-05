from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import AlertConfig, AlertMessage
from app.services.monitoring import MonitoringService
from app.utils.logger import logger

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertEndpoints:
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service

    @router.post("/configs")
    async def create_alert_config(self, config: AlertConfig):
        """创建告警配置"""
        try:
            result = await self.monitoring_service.add_alert_config(config)
            return {"status": "success", "config_id": result.id}
        except Exception as e:
            logger.error(f"创建告警配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/configs/{site_no}")
    async def get_site_alert_configs(self, site_no: str) -> List[AlertConfig]:
        """获取场站告警配置"""
        try:
            return await self.monitoring_service.get_alert_configs(site_no)
        except Exception as e:
            logger.error(f"获取告警配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/messages/{site_no}")
    async def get_site_alerts(
        self,
        site_no: str,
        start_time: str = None,
        end_time: str = None,
        alert_type: str = None
    ) -> List[AlertMessage]:
        """获取场站告警信息"""
        try:
            return await self.monitoring_service.get_alerts(
                site_no,
                start_time,
                end_time,
                alert_type
            )
        except Exception as e:
            logger.error(f"获取告警信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))