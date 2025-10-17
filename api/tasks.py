from celery import shared_task
from .metrics import MetricsFactory  # import your factory


@shared_task
def push_metrics():
    """Push metrics to Prometheus PushGateway periodically."""
    factory = MetricsFactory()
    provider = factory.provider
    provider.push()
