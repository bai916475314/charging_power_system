from fastapi import APIRouter, HTTPException

from app.models.schemas import ChargerProfileRequest
from app.services.database import DatabaseService
from app.utils.logger import logger

router = APIRouter(prefix="/chargers", tags=["chargers"])

class ChargerEndpoints:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    @router.post("/profiles")
    async def save_charger_profile(self, request: ChargerProfileRequest):
        """保存充电枪配置"""
        try:
            profile = await self.db_service.save_charger_profile(request.dict())
            return {"status": "success", "charger_sn": profile.charger_sn}
        except Exception as e:
            logger.error(f"保存充电枪配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))