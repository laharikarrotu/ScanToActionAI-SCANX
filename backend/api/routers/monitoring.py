"""
Monitoring and metrics endpoints
"""
from fastapi import APIRouter
from fastapi.responses import Response

from core.monitoring import get_prometheus_metrics
from core.logger import get_logger

logger = get_logger("api.routers.monitoring")
router = APIRouter(prefix="", tags=["monitoring"])

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring."""
    try:
        metrics_data = get_prometheus_metrics()
        try:
            from prometheus_client import CONTENT_TYPE_LATEST  # type: ignore[reportMissingImports]
            content_type = CONTENT_TYPE_LATEST
        except ImportError:
            content_type = "text/plain; version=0.0.4; charset=utf-8"
        
        return Response(
            content=metrics_data,
            media_type=content_type
        )
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        return Response(
            content=b"# Prometheus metrics unavailable\n",
            media_type="text/plain"
        )

