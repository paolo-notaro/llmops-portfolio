"""Tiny in-process metrics registry for the demo API."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    """Collect simple request and quality metrics."""

    request_count: int = 0
    latency_ms_total: float = 0.0
    evaluation_pass_count: int = 0
    retrieval_hit_count: int = 0
    latency_buckets: dict[str, int] = field(
        default_factory=lambda: {"le_50": 0, "le_100": 0, "le_250": 0, "le_500": 0, "gt_500": 0}
    )

    def record_request(self, latency_ms: float, *, evaluation_passed: bool, retrieval_hit: bool) -> None:
        """Record metrics for one request."""

        self.request_count += 1
        self.latency_ms_total += latency_ms
        self.evaluation_pass_count += int(evaluation_passed)
        self.retrieval_hit_count += int(retrieval_hit)
        if latency_ms <= 50:
            self.latency_buckets["le_50"] += 1
        elif latency_ms <= 100:
            self.latency_buckets["le_100"] += 1
        elif latency_ms <= 250:
            self.latency_buckets["le_250"] += 1
        elif latency_ms <= 500:
            self.latency_buckets["le_500"] += 1
        else:
            self.latency_buckets["gt_500"] += 1

    @property
    def average_latency_ms(self) -> float:
        """Average provider latency in milliseconds."""

        if self.request_count == 0:
            return 0.0
        return self.latency_ms_total / self.request_count

    @property
    def evaluation_pass_rate(self) -> float:
        """Fraction of requests that passed lightweight checks."""

        if self.request_count == 0:
            return 0.0
        return self.evaluation_pass_count / self.request_count

    @property
    def retrieval_hit_rate(self) -> float:
        """Fraction of requests with non-zero top retrieval score."""

        if self.request_count == 0:
            return 0.0
        return self.retrieval_hit_count / self.request_count

    def render_prometheus(self) -> str:
        """Render Prometheus-style text metrics."""

        lines = [
            "# HELP llmops_request_count Total API query requests.",
            "# TYPE llmops_request_count counter",
            f"llmops_request_count {self.request_count}",
            "# HELP llmops_average_latency_ms Average provider latency in milliseconds.",
            "# TYPE llmops_average_latency_ms gauge",
            f"llmops_average_latency_ms {self.average_latency_ms:.3f}",
            "# HELP llmops_evaluation_pass_rate Fraction of lightweight checks passing.",
            "# TYPE llmops_evaluation_pass_rate gauge",
            f"llmops_evaluation_pass_rate {self.evaluation_pass_rate:.3f}",
            "# HELP llmops_retrieval_hit_rate Fraction of requests with non-zero retrieval hit.",
            "# TYPE llmops_retrieval_hit_rate gauge",
            f"llmops_retrieval_hit_rate {self.retrieval_hit_rate:.3f}",
            "# HELP llmops_latency_bucket Synthetic latency buckets.",
            "# TYPE llmops_latency_bucket counter",
        ]
        for bucket, count in self.latency_buckets.items():
            lines.append(f'llmops_latency_bucket{{bucket="{bucket}"}} {count}')
        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()
