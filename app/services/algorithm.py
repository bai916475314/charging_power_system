from datetime import datetime
from typing import Dict, List

from app.models.schemas import PowerData
from app.utils.logger import logger


class VehicleRecognition:
    def recognize(self, **kwargs) -> str:
        """车型识别算法"""
        try:
            # 基于电压、电流、功率和容量特征进行识别
            voltage = kwargs.get('voltage')
            current = kwargs.get('current')
            power = kwargs.get('power')
            capacity = kwargs.get('capacity')

            # 实现车型识别逻辑
            # 这里需要根据具体的识别算法来实现
            return "default_model"  # 临时返回默认值

        except Exception as e:
            logger.error(f"车型识别失败: {str(e)}")
            raise


class PowerPrediction:
    def predict(self, power_data: PowerData) -> List[Dict]:
        """功率预测算法"""
        try:
            predictions = []
            current_soc = power_data.soc

            # 预测80%和90%SOC点的功率
            for target_soc in [80, 90]:
                if current_soc < target_soc:
                    # 计算预计充电时间和功率
                    time_to_target = self._calculate_charging_time(
                        current_soc,
                        target_soc,
                        power_data.power,
                        power_data.capacity
                    )
                    predicted_power = self._estimate_power(
                        power_data.power,
                        current_soc,
                        target_soc
                    )

                    predictions.append({
                        'target_soc': target_soc,
                        'time': time_to_target,
                        'power': predicted_power
                    })

            return predictions

        except Exception as e:
            logger.error(f"功率预测失败: {str(e)}")
            raise

    def _calculate_charging_time(
            self,
            current_soc: float,
            target_soc: float,
            current_power: float,
            capacity: float
    ) -> float:
        """计算充电时间"""
        soc_diff = target_soc - current_soc
        energy_needed = (capacity * soc_diff) / 100
        return energy_needed / current_power

    def _estimate_power(
            self,
            current_power: float,
            current_soc: float,
            target_soc: float
    ) -> float:
        """估算目标SOC点的功率"""
        # 简化模型，实际应该基于更复杂的充电曲线
        power_decay_rate = 0.95  # 假设每10%SOC功率降低5%
        soc_segments = (target_soc - current_soc) / 10
        return current_power * (power_decay_rate ** soc_segments)


class PowerOptimization:
    def optimize(
            self,
            site_info: Dict,
            charger_states: List[Dict]
    ) -> List[Dict]:
        """功率优化分配算法"""
        try:
            total_current_power = sum(
                state['current_power'] for state in charger_states
            )

            if total_current_power <= site_info['demand']:
                return charger_states  # 无需调整

            power_reduction = total_current_power - site_info['demand']

            # 计算最优分配
            optimized_powers = self._calculate_optimal_distribution(
                charger_states,
                power_reduction
            )

            # 生成调整方案
            profiles = []
            for charger_sn, new_power in optimized_powers.items():
                profiles.append({
                    'charger_sn': charger_sn,
                    'power': new_power,
                    'timestamp': datetime.utcnow().isoformat()
                })

            return profiles

        except Exception as e:
            logger.error(f"功率优化失败: {str(e)}")
            raise

    def _calculate_optimal_distribution(
            self,
            charger_states: List[Dict],
            power_reduction: float
    ) -> Dict[str, float]:
        """计算最优功率分配"""
        # 按功率从大到小排序
        sorted_chargers = sorted(
            charger_states,
            key=lambda x: x['current_power'],
            reverse=True
        )

        adjustments = {}
        remaining_reduction = power_reduction

        for charger in sorted_chargers:
            current_power = charger['current_power']
            min_power = current_power * 0.7  # 最大下调30%

            if remaining_reduction <= 0:
                adjustments[charger['charger_sn']] = current_power
                continue

            # 计算可调整量
            max_adjustment = current_power - min_power
            actual_adjustment = min(max_adjustment, remaining_reduction)

            # 如果调整小于10%，不计入影响
            if actual_adjustment / current_power < 0.1:
                adjustments[charger['charger_sn']] = current_power
                continue

            new_power = current_power - actual_adjustment
            adjustments[charger['charger_sn']] = new_power
            remaining_reduction -= actual_adjustment

        return adjustments