from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.schemas import SiteInfoRequest, SiteResponse
from app.services.algorithm import AlgorithmService
from app.services.database import DatabaseService
from app.services.maintenance import MaintenanceService
from app.utils.logger import logger

router = APIRouter(prefix="/sites", tags=["sites"])


class SiteEndpoints:
    def __init__(
            self,
            db_service: DatabaseService,
            algorithm_service: AlgorithmService,
            maintenance_service: MaintenanceService
    ):
        self.db_service = db_service
        self.algorithm_service = algorithm_service
        self.maintenance_service = maintenance_service

    @router.post("/", response_model=SiteResponse)
    async def handle_site_info(
            self,
            request: SiteInfoRequest,
            background_tasks: BackgroundTasks
    ):
        """处理场站信息接口"""
        try:
            # 1. 获取历史场站信息
            old_site = await self.db_service.get_site_info(request.site_no)

            # 2. 存储新的场站信息
            site = await self.db_service.save_site_info(request.dict())

            # 3. 检查demand变化并触发功率重新分配
            if old_site and old_site.demand != request.demand:
                logger.info(f"场站 {request.site_no} 的demand值发生变化")
                background_tasks.add_task(
                    self.algorithm_service.trigger_power_optimization,
                    request.site_no
                )

            # 4. 通知运维平台（异步执行）
            pile_sns = [pile.pile_sn for pile in request.piles]
            background_tasks.add_task(
                self.maintenance_service.notify_maintenance,
                request.site_no,
                pile_sns
            )

            return SiteResponse(
                status="success",
                site_id=site.site_no
            )

        except Exception as e:
            logger.error(f"处理场站信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))