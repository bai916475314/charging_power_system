import asyncio
from datetime import datetime
from typing import Dict

from app.core.config import settings
from app.models.schemas import AlertMessage
from app.services.database import DatabaseService
from app.utils.logger import logger


class MonitoringService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.alert_configs = {}
        self._running = False

    async def start(self):
        """启动监控服务"""
        self._running = True
        await self._load_alert_configs()
        asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """停止监控服务"""
        self._running = False

    async def _monitoring_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 获取所有场站状态
                sites = await self.db_service.get_all_active_sites()

                for site in sites:
                    # 检查场站状态
                    await self._check_site_status(site)
                    # 检查充电桩状态
                    await self._check_charger_status(site.site_no)
                    # 检查功率分配
                    await self._check_power_allocation(site.site_no)

                await asyncio.sleep(settings.MONITORING_INTERVAL)

            except Exception as e:
                logger.error(f"监控循环异常: {str(e)}")
                await asyncio.sleep(5)

    async def _check_site_status(self, site: Dict):
        """检查场站状态"""
        try:
            # 检查总功率是否超限
            if site['current_power'] > site['total_power_limit']:
                await self._create_alert(
                    site_no=site['site_no'],
                    alert_type="POWER_EXCEED",
                    message=f"场站总功率超限: {site['current_power']}kW > {site['total_power_limit']}kW"
                )

            # 检查需求响应
            if site['current_power'] > site['demand']:
                await self._create_alert(
                    site_no=site['site_no'],
                    alert_type="DEMAND_EXCEED",
                    message=f"场站功率超过需求: {site['current_power']}kW > {site['demand']}kW"
                )

        except Exception as e:
            logger.error(f"场站状态检查失败: {str(e)}")

    async def _check_charger_status(self, site_no: str):
        """检查充电桩状态"""
        try:
            chargers = await self.db_service.get_charger_states(site_no)

            for charger in chargers:
                # 检查充电异常
                if charger['status'] == 'ERROR':
                    await self._create_alert(
                        site_no=site_no,
                        alert_type="CHARGER_ERROR",
                        message=f"充电桩故障: {charger['charger_sn']}"
                    )

                # 检查功率异常
                if charger['current_power'] > charger['rated_power']:
                    await self._create_alert(
                        site_no=site_no,
                        alert_type="CHARGER_POWER_EXCEED",
                        message=f"充电桩功率超限: {charger['charger_sn']}"
                    )

        except Exception as e:
            logger.error(f"充电桩状态检查失败: {str(e)}")

    async def _create_alert(self, site_no: str, alert_type: str, message: str):
        """创建告警"""
        try:
            alert = AlertMessage(
                site_no=site_no,
                alert_type=alert_type,
                message=message,
                created_at=datetime.utcnow()
            )
            await self.db_service.save_alert(alert)
            logger.warning(f"创建告警: {message}")

        except Exception as e:
            logger.error(f"创建告警失败: {str(e)}")