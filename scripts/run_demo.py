"""Run the local LLMOps evaluation demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llmops_portfolio.config import load_settings
from llmops_portfolio.evaluators import evaluate_examples
from llmops_portfolio.models import EvaluationExample
from llmops_portfolio.providers import provider_from_env
from llmops_portfolio.rag import LocalTfidfRAGIndex
from llmops_portfolio.report import write_report


def load_evaluation_examples(eval_dir: Path) -> list[EvaluationExample]:
    """Load all JSONL examples from the evaluation directory."""

    examples: list[EvaluationExample] = []
    for path in sorted(eval_dir.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip():
                payload = json.loads(line)
                examples.append(EvaluationExample(**payload))
            else:
                raise ValueError(f"Blank line in {path}:{line_number}")
    return examples


def main() -> None:
    """Run the complete local evaluation workflow."""

    console = Console()
    settings = load_settings()
    index = LocalTfidfRAGIndex.from_directory(settings.docs_dir)
    provider = provider_from_env(settings.llm_provider)
    examples = load_evaluation_examples(settings.eval_dir)
    report = evaluate_examples(
        examples,
        index,
        provider,
        top_k=3,
        max_latency_ms=settings.max_latency_ms,
        config={
            "provider": provider.name,
            "docs_dir": str(settings.docs_dir),
            "eval_dir": str(settings.eval_dir),
            "top_k": 3,
            "max_latency_ms": settings.max_latency_ms,
        },
    )
    json_path, markdown_path = write_report(report, settings.reports_dir)
    print_summary(console, report)
    console.print(f"\nReports written: {json_path} and {markdown_path}")
    console.print(f"Predictions: {settings.reports_dir / 'evaluation_predictions.jsonl'}")
    console.print(f"Metrics: {settings.reports_dir / 'evaluation_metrics.json'}")


def print_summary(console: Console, report) -> None:
    """Print a concise terminal summary."""

    table = Table(title="LLMOps Evaluation Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Threshold", justify="right")
    for metric in report.summary.quality_metrics:
        table.add_row(metric.label, f"{metric.value:.3f}", f"{metric.threshold:.3f}")
    console.print(table)
    console.print(f"Total examples: {report.summary.total_examples}")
    console.print(f"Readiness score: {report.summary.pass_rate:.3f}")
    console.print(f"Average latency: {report.summary.average_latency_ms:.3f} ms")
    console.print(f"p95 latency: {report.summary.latency_p95_ms:.3f} ms")
    console.print(f"Examples requiring review: {report.summary.review_count}")


if __name__ == "__main__":
    main()
