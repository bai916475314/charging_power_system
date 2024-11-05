from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel


class AlertConfig(BaseModel):
    site_no: str
    alert_type: str
    threshold: float
    description: str
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

class AlertMessage(BaseModel):
    site_no: str
    alert_type: str
    message: str
    severity: str
    status: str = "ACTIVE"
    created_at: datetime
    resolved_at: Optional[datetime] = None

class PowerStatistics(BaseModel):
    site_no: str
    total_power: float
    max_power: float
    min_power: float
    avg_power: float
    demand_satisfaction_rate: float
    time_range: str
    data_points: List[Dict[str, float]]
    updated_at: datetime

class OptimizationStatistics(BaseModel):
    site_no: str
    total_tasks: int
    success_rate: float
    avg_power_reduction: float
    affected_chargers: int
    energy_saved: float
    period: str
    updated_at: datetime