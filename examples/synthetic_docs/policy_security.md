# Synthetic Security Policy

This synthetic policy defines representative controls for a local-first LLM application. It is not based on any employer policy or customer environment.

## Prompt Safety

Requests that ask for credential theft, malware instructions, bypassing access controls, or exfiltrating private data must be refused. The assistant should provide a brief explanation and redirect to safe operational guidance.

## Data Handling

Evaluation datasets must use synthetic or explicitly approved public data. Secrets, customer records, private incident details, and proprietary prompts must not be committed to source control.

## Observability

Logs should avoid storing raw secrets or unnecessary personal data. Metrics should track request volume, latency, safety failures, retrieval hit rate, and evaluation pass rate.
