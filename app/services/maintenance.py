from datetime import datetime
from typing import List

import httpx

from app.core.config import settings
from app.utils.logger import logger


class MaintenanceService:
    def __init__(self):
        self.base_url = settings.MAINTENANCE_API_URL
        self.timeout = settings.MAINTENANCE_API_TIMEOUT

    async def notify_maintenance(self, site_no: str, pile_sns: List[str]):
        """通知运维平台上报数据"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/notify",
                    json={
                        "site_no": site_no,
                        "pile_sns": pile_sns,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                response.raise_for_status()
                logger.info(f"成功通知运维平台: {site_no}, {pile_sns}")
                return response.json()
        except Exception as e:
            logger.error(f"通知运维平台失败: {str(e)}")
            raise