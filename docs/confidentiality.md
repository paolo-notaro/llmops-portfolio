# Confidentiality

This repository is a public, privacy-safe demonstration. It is not employer code, not a clone of a private platform, and not derived from confidential datasets or proprietary architecture.

## What Is Included

- Synthetic Markdown documents.
- Synthetic evaluation examples.
- Deterministic mock provider responses.
- Representative evaluation and observability patterns.
- Sanitized case studies written at the level of public engineering practice.

## What Is Omitted

- Customer data, production prompts, internal logs, traces, and tickets.
- Private model configurations or deployment details.
- Employer-specific product names or confidential architecture.
- Exact incident details, metrics, thresholds, or operational runbooks.
- Real API calls in the default path.

## Provider Integrations

The default provider is `mock`. Environment variables for real providers are documented only as placeholders:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

The demo does not require those keys and does not make network calls in tests or default execution.
