from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Site(Base):
    __tablename__ = 'site'

    site_no = Column(String(50), primary_key=True, comment='场站ID')
    name = Column(String(100), nullable=False)
    total_power_limit = Column(Float, nullable=False)
    demand = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 关系定义
    charger_groups = relationship("ChargerGroup", back_populates="site")
    optimization_tasks = relationship("OptimizationTask", back_populates="site")


class ChargerGroup(Base):
    __tablename__ = 'charger_group'

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    site_no = Column(String(50), ForeignKey('site.site_no'), nullable=False)
    power_limit = Column(Float, nullable=False, comment='群组上限')
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    site = relationship("Site", back_populates="charger_groups")
    piles = relationship("Pile", back_populates="group")


class Pile(Base):
    __tablename__ = 'pile'

    pile_sn = Column(String(50), primary_key=True)
    group_id = Column(Integer, ForeignKey('charger_group.group_id'))
    type = Column(String(50))
    rated_power = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    group = relationship("ChargerGroup", back_populates="piles")
    modules = relationship("Module", back_populates="pile")
    chargers = relationship("Charger", back_populates="pile")


class Charger(Base):
    __tablename__ = 'charger'

    charger_sn = Column(String(50), primary_key=True, comment='枪SN')
    pile_sn = Column(String(50), ForeignKey('pile.pile_sn'), comment='桩SN')
    status = Column(String(20), comment='插、拔枪状态')
    max_power = Column(Float, comment='上限')
    min_power = Column(Float, comment='下限')
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    pile = relationship("Pile", back_populates="chargers")
    charging_sessions = relationship("ChargingSession", back_populates="charger")


class Module(Base):
    __tablename__ = 'module'

    id = Column(Integer, primary_key=True, autoincrement=True)
    pile_sn = Column(String(50), ForeignKey('pile.pile_sn'), comment='桩SN')
    type = Column(String(50))
    module_no = Column(Integer)
    unit_power = Column(Integer)

    # 关系定义
    pile = relationship("Pile", back_populates="modules")


class EVModel(Base):
    __tablename__ = 'ev_model'

    session_id = Column(String(50), primary_key=True, comment='充电任务')
    mac_addr = Column(String(50), nullable=False, comment='mac')
    capacity = Column(Float, comment='电池容量')
    max_voltage = Column(Float, comment='最大电压')
    max_current = Column(Float, comment='最大电流')
    max_power = Column(Float, comment='最大功率')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    report_at = Column(DateTime, comment='上报时间')
    vendor_model_capacity = Column(String(100), comment='车型识别结果')

    # 关系定义
    charging_sessions = relationship("ChargingSession", back_populates="ev_model")
    power_predictions = relationship("PowerPrediction", back_populates="ev_model")


class ChargingSession(Base):
    __tablename__ = 'charging_session'

    session_id = Column(String(50), primary_key=True, comment='充电任务')
    charger_sn = Column(String(50), ForeignKey('charger.charger_sn'), comment='枪SN')
    mac_addr = Column(String(50), ForeignKey('ev_model.mac_addr'), comment='电池的MAC地址')
    start_time = Column(DateTime, comment='插枪时间')
    end_time = Column(DateTime, comment='策略完成时间')
    total_energy = Column(Float)
    status = Column(String(20), comment='充电任务状态，充电中')

    # 关系定义
    charger = relationship("Charger", back_populates="charging_sessions")
    ev_model = relationship("EVModel", back_populates="charging_sessions")
    charging_records = relationship("ChargingRecord", back_populates="charging_session")


class PowerPrediction(Base):
    __tablename__ = 'power_prediction'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('ev_model.session_id'), comment='充电任务')
    charger_sn = Column(String(50), comment='枪SN')
    mac_addr = Column(String(50), comment='电池MAC')
    time = Column(Float, comment='时间')
    power = Column(Float, comment='功率')

    # 关系定义
    ev_model = relationship("EVModel", back_populates="power_predictions")


class ChargingRecord(Base):
    __tablename__ = 'charging_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('charging_session.session_id'), comment='充电任务')
    mac_addr = Column(String(50), comment='电池地址')
    charger_sn = Column(String(50), comment='枪SN')
    timestamp = Column(DateTime, comment='上报时间')
    curr_output = Column(Float, comment='实际电流')
    vol_output = Column(Float, comment='实际电压')
    curr_demand = Column(Float, comment='需求电流')
    soc = Column(Float)
    vol_demand = Column(Float, comment='需求电压')
    consumed_energy = Column(Float, comment='累计能耗')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    report_at = Column(DateTime, comment='上报时间')

    # 关系定义
    charging_session = relationship("ChargingSession", back_populates="charging_records")


class OptimizationTask(Base):
    __tablename__ = 'optimization_task'

    task_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), comment='充电任务')
    site_no = Column(String(50), ForeignKey('site.site_no'))
    demand = Column(Float)
    vendor_model_capacity = Column(String(100), comment='车型识别结果')
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    limit_json = Column(JSON, comment='限制条件JSON')
    pile_power_json = Column(JSON, comment='桩功率分配JSON')
    task_type = Column(Integer, comment='功率分配算法类型 智能分配/快速分配')

    # 关系定义
    site = relationship("Site", back_populates="optimization_tasks")