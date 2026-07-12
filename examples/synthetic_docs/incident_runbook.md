# Synthetic Incident Runbook

This runbook describes a representative workflow for an AI system incident using synthetic details only.

## Triage

Confirm the user-facing symptom, affected endpoint, approximate start time, and recent deployment events. Assign an incident lead and record decisions in a structured timeline.

## Investigation

Compare latency, error rate, retrieval hit rate, evaluation pass rate, and provider response patterns. Separate retrieval failures from generation failures before changing prompts or model settings.

## Mitigation

If a recent deployment caused the regression, roll back the application version or route traffic away from the failing provider. Keep the change small and monitor recovery before closing the incident.
