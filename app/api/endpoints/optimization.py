from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.schemas import OptimizationRequest, OptimizationResponse
from app.services.algorithm import AlgorithmService
from app.services.database import DatabaseService
from app.utils.logger import logger

router = APIRouter(prefix="/optimization", tags=["optimization"])


class OptimizationEndpoints:
    def __init__(
            self,
            algorithm_service: AlgorithmService,
            db_service: DatabaseService
    ):
        self.algorithm_service = algorithm_service
        self.db_service = db_service

    @router.post("/tasks", response_model=OptimizationResponse)
    async def create_optimization_task(
            self,
            request: OptimizationRequest,
            background_tasks: BackgroundTasks
    ):
        """创建优化任务"""
        try:
            # 获取场站信息
            site = await self.db_service.get_site_info(request.site_no)
            if not site:
                raise HTTPException(status_code=404, detail="场站不存在")

            # 获取充电枪状态
            charger_states = await self.db_service.get_charger_states(request.site_no)

            # 在后台执行优化
            background_tasks.add_task(
                self.algorithm_service.trigger_power_optimization,
                site,
                charger_states
            )

            return OptimizationResponse(
                status="success",
                message="优化任务已创建",
                site_no=request.site_no
            )

        except Exception as e:
            logger.error(f"创建优化任务失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/tasks/{site_no}/history")
    async def get_optimization_history(self, site_no: str):
        """获取优化任务历史"""
        try:
            tasks = await self.db_service.get_optimization_tasks(site_no)
            return {
                "site_no": site_no,
                "tasks": tasks
            }
        except Exception as e:
            logger.error(f"获取优化任务历史失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/tasks/{task_id}")
    async def get_optimization_task(self, task_id: int):
        """获取优化任务详情"""
        try:
            task = await self.db_service.get_optimization_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")
            return task
        except Exception as e:
            logger.error(f"获取优化任务详情失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))