from datetime import datetime
from typing import List, Dict

from app.models.entities import Site
from app.utils.logger import logger


class PowerOptimization:
    def __init__(self):
        self.solver = None  # 可以使用如 pulp 等优化库

    async def optimize(
            self,
            site_info: Site,
            charger_states: List[Dict]
    ) -> List[Dict]:
        """
        功率优化分配
        - 目标：最小化受影响充电枪数量
        - 约束：功率下降不超过30%，10%以下不计入影响
        """
        try:
            # 1. 计算当前总功率
            total_current_power = sum(state['current_power'] for state in charger_states)

            # 2. 计算需要减少的功率
            power_reduction = total_current_power - site_info.demand
            if power_reduction <= 0:
                return charger_states  # 无需调整

            # 3. 计算每个充电枪的新功率
            adjusted_powers = self._calculate_optimal_distribution(
                charger_states,
                power_reduction,
                site_info.demand
            )

            # 4. 生成调整方案
            profiles = []
            for charger, new_power in adjusted_powers.items():
                profile = {
                    "charger_sn": charger,
                    "power": new_power,
                    "timestamp": datetime.utcnow().isoformat()
                }
                profiles.append(profile)

            return profiles

        except Exception as e:
            logger.error(f"功率优化失败: {str(e)}")
            raise

    def _calculate_optimal_distribution(
            self,
            charger_states: List[Dict],
            power_reduction: float,
            target_demand: float
    ) -> Dict[str, float]:
        """计算最优功率分配"""
        # 1. 按功率从大到小排序
        sorted_chargers = sorted(
            charger_states,
            key=lambda x: x['current_power'],
            reverse=True
        )

        # 2. 计算每个充电枪的最大可调整功率
        adjustments = {}
        remaining_reduction = power_reduction

        for charger in sorted_chargers:
            current_power = charger['current_power']
            min_power = current_power * 0.7  # 最大下调30%
            max_adjustment = current_power - min_power

            if remaining_reduction <= 0:
                break

            # 计算实际调整量
            actual_adjustment = min(max_adjustment, remaining_reduction)
            remaining_reduction -= actual_adjustment

            # 记录新功率
            new_power = current_power - actual_adjustment
            adjustments[charger['charger_sn']] = new_power

        return adjustments