from typing import List, Dict

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.algorithm import AlgorithmService
from app.services.database import DatabaseService
from app.utils.logger import logger

router = APIRouter()


class HTTPService:
    def __init__(
            self,
            db_service: DatabaseService,
            algorithm_service: AlgorithmService
    ):
        self.db_service = db_service
        self.algorithm_service = algorithm_service
        self.previous_demands = {}  # 存储历史demand值

    @router.post("/sites/info")
    async def handle_site_info(self, request: Dict):
        """处理场站信息"""
        try:
            # 请求验证
            self._validate_request(request)

            site_no = request.get('site_no')
            current_demand = request.get('demand')

            # 检查demand变化
            if site_no in self.previous_demands:
                if self.previous_demands[site_no] != current_demand:
                    logger.info(f"场站 {site_no} 的demand值发生变化，触发功率重新分配")
                    await self.algorithm_service.trigger_power_optimization(site_no)

            # 更新历史demand值
            self.previous_demands[site_no] = current_demand

            # 存储场站信息
            site = await self.db_service.save_site_info(request)

            # 通知运维平台
            await self.notify_maintenance([pile['pile_sn'] for pile in request.get('piles', [])])

            return {"status": "success", "site_id": site.site_no}

        except Exception as e:
            logger.error(f"处理场站信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def notify_maintenance(self, piles: List[str]):
        """通知运维平台"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.MAINTENANCE_API_URL}/notify",
                    json={"pile_sns": piles}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"通知运维平台失败: {str(e)}")
            raise

    def _validate_request(self, request: Dict) -> bool:
        """验证请求数据"""
        required_fields = ['site_no', 'demand', 'total_power_limit']
        for field in required_fields:
            if field not in request:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少必要字段: {field}"
                )
        return True

    @router.get("/sites/{site_no}")
    async def get_site_info(self, site_no: str):
        """获取场站信息"""
        try:
            site = await self.db_service.get_site_info(site_no)
            if not site:
                raise HTTPException(status_code=404, detail="场站不存在")
            return site
        except Exception as e:
            logger.error(f"获取场站信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))