import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Exporters
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# from opentelemetry.exporter.zipkin.json import ZipkinExporter
# OTLP exporter works for multiple backends
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from abc import abstractmethod, ABC


class Traceble(ABC):
    @abstractmethod
    def trace(self):
        pass

    @abstractmethod
    def name(self):
        pass


class JaegerTraceble(Traceble):
    def trace(self):
        return JaegerExporter(
            agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_PORT", 6831)),
        )

    def name(self):
        return "jaeger"


class ExporterRegistry:
    _registry = {
        "jaeger": JaegerTraceble(),
        # Future implementations can be added here
    }

    @classmethod
    def get_exporter(cls, name: str) -> Traceble:
        exporter = cls._registry.get(name.lower())
        if not exporter:
            raise ValueError(f"Unsupported exporter: {name}")
        return exporter.trace()


class TracerFactory:
    _initialized = False  # Prevent multiple initializations

    @classmethod
    def make_tracer(cls) -> Traceble:
        if cls._initialized:
            return
        # Step 1: Set tracer provider
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({"service.name": "UserAuthService"})
            )
        )
        tracer_provider = trace.get_tracer_provider()

        # Step 2: Choose exporter from env variable
        backend = os.getenv("OTEL_TRACER_BACKEND", "jaeger").lower()
        exporter = ExporterRegistry.get_exporter(backend)
        # Step 3: Add span processor
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)

        cls._initialized = True

        return trace.get_tracer(__name__)
