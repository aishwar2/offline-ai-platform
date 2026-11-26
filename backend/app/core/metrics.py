"""Prometheus instrumentation metrics for API, token usage, and LLM latency."""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "offline_ai_http_requests_total",
    "Total HTTP requests handled by the backend API",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "offline_ai_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

LLM_TOKENS_TOTAL = Counter(
    "offline_ai_llm_tokens_total",
    "Total tokens processed by local Ollama models",
    ["model", "token_type"],
)

LLM_RESPONSE_DURATION_SECONDS = Histogram(
    "offline_ai_llm_response_duration_seconds",
    "End-to-end model inference duration in seconds",
    ["model"],
    buckets=(0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 40.0, 60.0, 120.0),
)

ACTIVE_CONVERSATIONS = Gauge(
    "offline_ai_active_conversations",
    "Total stored conversations in the platform",
)
