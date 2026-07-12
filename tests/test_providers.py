from llmops_portfolio.models import RetrievedDocument
from llmops_portfolio.providers import MockLLMProvider


def test_mock_provider_returns_deterministic_answer_text() -> None:
    provider = MockLLMProvider()
    contexts = [
        RetrievedDocument(
            doc_id="deployment_guide",
            title="Synthetic Deployment Guide",
            path="examples/synthetic_docs/deployment_guide.md",
            chunk_id="deployment_guide-1",
            text="Rollback should restore the previous application version and retrieval settings.",
            score=0.9,
        )
    ]

    first = provider.generate("How should rollback work?", contexts)
    second = provider.generate("How should rollback work?", contexts)

    assert first.answer == second.answer
    assert "[doc:deployment_guide]" in first.answer
