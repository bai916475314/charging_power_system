from fastapi import APIRouter

from app.api.endpoints import site, charger, optimization, monitoring

# 创建主路由
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    site.router,
    prefix="/sites",
    tags=["sites"]
)

api_router.include_router(
    charger.router,
    prefix="/chargers",
    tags=["chargers"]
)

api_router.include_router(
    optimization.router,
    prefix="/optimization",
    tags=["optimization"]
)

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)