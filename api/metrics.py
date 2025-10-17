from abc import ABC, abstractmethod
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    push_to_gateway,
    CollectorRegistry,
)
import time
import os


class Countable(ABC):
    @abstractmethod
    def increment(self, labels=None):
        pass


class Observable(ABC):
    @abstractmethod
    def observe(self, value, labels=None):
        pass


class Guageable(ABC):
    @abstractmethod
    def set(self, value, labels=None):
        pass


class PrometheusCounterWrapper(Countable):
    def __init__(self, counter):
        self.counter = counter

    def increment(self, labels=None):
        if labels:
            self.counter.labels(**labels).inc()
        else:
            self.counter.inc()


class PrometheusGaugeWrapper(Guageable):
    def __init__(self, gauge):
        self.gauge = gauge

    def set(self, value, labels=None):
        if labels:
            self.gauge.labels(**labels).set(value)
        else:
            self.gauge.set(value)


class PrometheusHistogramWrapper(Observable):
    def __init__(self, histogram):
        self.histogram = histogram

    def observe(self, value, labels=None):
        if labels:
            self.histogram.labels(**labels).observe(value)
        else:
            self.histogram.observe(value)


class MetricsProvider(ABC):
    """Abstract metrics provider for easy backend swapping."""

    @abstractmethod
    def counter(self, name: str, description: str):
        """Return a counter metric."""
        pass

    @abstractmethod
    def gauge(self, name: str, description: str):
        """Return a gauge metric."""
        pass

    @abstractmethod
    def histogram(self, name: str, description: str, buckets=None):
        """Return a histogram metric."""
        pass

    @abstractmethod
    def push(self):
        """Push all metrics to the configured backend."""
        pass


class PrometheusMetric(MetricsProvider):
    def __init__(self, job_name="user-auth-service", pushgateway=None):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self.job_name = job_name
        self.pushgateway = pushgateway or os.getenv("PROMETHEUS_PUSHGATEWAY")

    def counter(self, name, description, labelnames=()):
        if name not in self.metrics:
            counter_obj = Counter(name, description, labelnames, registry=self.registry)
        self.metrics[name] = PrometheusCounterWrapper(counter_obj)
        return self.metrics[name]

    def histogram(self, name, description, labelnames=(), buckets=None):
        if name not in self.metrics:
            hist_obj = Histogram(
                name, description, labelnames, buckets=buckets, registry=self.registry
            )
        self.metrics[name] = PrometheusHistogramWrapper(hist_obj)
        return self.metrics[name]

    def gauge(self, name, description, labelnames=()):
        if name not in self.metrics:
            self.metrics[name] = Gauge(
                name, description, labelnames, registry=self.registry
            )
        return self.metrics[name]

    def push(self):
        """Push metrics to Prometheus PushGateway if configured."""
        if self.pushgateway:
            push_to_gateway(self.pushgateway, job=self.job_name, registry=self.registry)


class AbstractMetricsFactory(ABC):

    @abstractmethod
    def create_counter(self, name, documentation, labelnames=()):
        pass

    @abstractmethod
    def create_histogram(self, name, documentation, labelnames=(), buckets=None):
        pass


class MetricsRegistryError:
    _registry = {
        "prometheus": PrometheusMetric,
        # future providers can be added here
    }

    @classmethod
    def get(cls, provider_name):
        if provider_name in cls._registry:
            return cls._registry[provider_name]
        raise ValueError(f"Metrics provider '{provider_name}' not found.")


class MetricsFactory(AbstractMetricsFactory):

    def __init__(self):
        self.provider = self.get_provider_backend() or PrometheusMetric()

    def create_counter(self, name, documentation, labelnames=()):
        return self.provider.counter(name, documentation, labelnames)

    def create_histogram(self, name, documentation, labelnames=(), buckets=None):
        return self.provider.histogram(name, documentation, labelnames, buckets)

    def get_provider_backend(self):
        backend_name = os.getenv("METRICS_BACKEND", "prometheus").lower()
        provider_cls = MetricsRegistryError.get(backend_name)
        return provider_cls()  # instantiate


class AbstractViewMetrics(ABC):
    @property
    @abstractmethod
    def counter(self):
        pass

    @property
    @abstractmethod
    def latency(self):
        pass

    @property
    @abstractmethod
    def factory(self):
        pass


class GeneralMetricsView(AbstractViewMetrics, ABC):
    factory = MetricsFactory()

    def __init__(self):
        self._counter = self.factory.create_counter(
            name=f"{self.name}_total",
            documentation=f"Total number of {self.name if not self.documentation else self.documentation} attempts",
            labelnames=self.labelnames,
        )

        self._latency = self.factory.create_histogram(
            name=f"{self.name}_latency_seconds",
            documentation="Time taken to process {self.name if not self.documentation else self.documentation} requests",
            labelnames=self.labelnames,
            buckets=self.buckets,
        )

    @property
    def counter(self):
        return self._counter

    @property
    def latency(self):
        return self._latency

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    def documentation(self):
        return f"Metrics for {self.name} operations"

    @property
    def labelnames(self):
        return ("status", "method")

    @property
    def buckets(self):
        return [0.1, 0.5, 1, 2, 5]


class RegistrationMetrics(GeneralMetricsView):
    name = "user_registration"


class LoginMetrics(GeneralMetricsView):
    name = "user_login"


class LogoutMetrics(GeneralMetricsView):
    name = "user_logout"


class PasswordResetRequestMetrics(GeneralMetricsView):
    name = "password_reset_request"


class ThirdPartyLoginMetrics(GeneralMetricsView):
    name = "third_party_login"


class ThirdPartyRegisterMetrics(GeneralMetricsView):
    name = "third_party_registration"


class TokenRefreshMetrics(GeneralMetricsView):
    name = "token_refresh"


class TokenValidationMetrics(GeneralMetricsView):
    name = "token_validation"


"""
The decorator to track metrics for DRF views.
"""


def track_metrics(get_metrics):
    def decorator(func):
        def wrapper(view, request, *args, **kwargs):
            metrics = get_metrics(view)
            start = time.time()
            response = None
            try:
                response = func(view, request, *args, **kwargs)
                return response
            finally:
                elapsed = time.time() - start
                labels = {
                    "status": str(response.status_code) if response else "500",
                    "method": request.method,
                }
                metrics.counter.increment(labels=labels)
                metrics.latency.observe(elapsed, labels=labels)

        return wrapper

    return decorator
