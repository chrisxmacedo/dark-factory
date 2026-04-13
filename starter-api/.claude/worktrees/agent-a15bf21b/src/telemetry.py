"""OpenTelemetry initialization for Axiom observability."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.config import Settings

_provider: TracerProvider | None = None


def init_telemetry(settings: Settings) -> None:
    global _provider
    if not settings.axiom_token:
        return

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "0.1.0",
            "deployment.environment": settings.app_env,
        }
    )
    _provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint="https://api.axiom.co/v1/traces",
        headers={
            "Authorization": f"Bearer {settings.axiom_token}",
            "X-Axiom-Dataset": settings.axiom_dataset,
        },
    )
    _provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(_provider)


def instrument_app(app: object, sync_engine: object) -> None:
    if _provider is None:
        return
    FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    SQLAlchemyInstrumentor().instrument(engine=sync_engine)


def shutdown_telemetry() -> None:
    if _provider is not None:
        _provider.shutdown()
