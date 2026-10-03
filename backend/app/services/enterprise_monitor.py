"""Steps 29-30: Enterprise Monitoring & System Health.

Production monitoring:
- API health checks
- Data freshness validation
- Cache hit rates
- Error tracking and alerting

Input: System metrics
Output: HealthReport (system status)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    """Health of single service."""
    service_name: str
    status: str  # "Healthy", "Degraded", "Down"
    uptime_pct: float
    error_count: int
    last_check: str


@dataclass
class HealthReport:
    """System health report."""
    timestamp: str
    overall_status: str  # "Healthy", "Degraded", "Down"
    services: List[ServiceHealth] = field(default_factory=list)

    api_calls_total: int = 0
    api_errors: int = 0
    cache_hit_rate: float = 0.0

    data_freshness: Dict[str, str] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "status": self.overall_status,
            "api_health": {
                "total_calls": self.api_calls_total,
                "error_rate": round(
                    (self.api_errors / self.api_calls_total * 100)
                    if self.api_calls_total > 0
                    else 0,
                    1,
                ),
            },
            "cache_hit_rate": round(self.cache_hit_rate, 1),
            "services": [
                {
                    "name": s.service_name,
                    "status": s.status,
                    "uptime": round(s.uptime_pct, 1),
                }
                for s in self.services
            ],
            "alerts": self.alerts,
        }


class EnterpriseMonitor:
    """Monitors system health."""

    def __init__(self):
        """Initialize monitor."""
        self.logger = logging.getLogger(__name__)

    def generate_health_report(
        self,
        services_status: Dict[str, Dict[str, Any]],
        api_metrics: Dict[str, Any],
    ) -> HealthReport:
        """Generate system health report.

        Args:
            services_status: {service_name: {status, uptime_pct, errors}}
            api_metrics: {calls_total, errors, cache_hit_rate}

        Returns:
            HealthReport with system status
        """
        try:
            report = HealthReport(
                timestamp=datetime.now().isoformat(),
                overall_status="Healthy",
                api_calls_total=api_metrics.get("calls_total", 0),
                api_errors=api_metrics.get("errors", 0),
                cache_hit_rate=api_metrics.get("cache_hit_rate", 0.0),
            )

            # Check each service
            for service_name, status_data in services_status.items():
                service = ServiceHealth(
                    service_name=service_name,
                    status=status_data.get("status", "Unknown"),
                    uptime_pct=status_data.get("uptime_pct", 0.0),
                    error_count=status_data.get("error_count", 0),
                    last_check=datetime.now().isoformat(),
                )
                report.services.append(service)

                # Update overall status
                if service.status == "Down":
                    report.overall_status = "Down"
                elif service.status == "Degraded" and report.overall_status == "Healthy":
                    report.overall_status = "Degraded"

            # Generate alerts
            report.alerts = self._generate_alerts(report)

            self.logger.info(
                f"Health report: {report.overall_status} "
                f"({len(report.services)} services)"
            )
            return report

        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return HealthReport(timestamp=datetime.now().isoformat())

    @staticmethod
    def _generate_alerts(report: HealthReport) -> List[str]:
        """Generate alerts from report."""
        alerts = []

        # API error rate
        if report.api_calls_total > 0:
            error_rate = (report.api_errors / report.api_calls_total) * 100
            if error_rate > 5:
                alerts.append(f"High API error rate: {error_rate:.1f}%")

        # Cache hit rate
        if report.cache_hit_rate < 30:
            alerts.append(
                f"Low cache hit rate: {report.cache_hit_rate:.1f}%"
            )

        # Service status
        for service in report.services:
            if service.status == "Down":
                alerts.append(f"Service down: {service.service_name}")
            elif service.status == "Degraded":
                alerts.append(f"Service degraded: {service.service_name}")
            elif service.uptime_pct < 95:
                alerts.append(
                    f"Low uptime: {service.service_name} "
                    f"({service.uptime_pct:.1f}%)"
                )

        return alerts
