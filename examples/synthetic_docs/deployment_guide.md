# Synthetic Deployment Guide

This guide describes representative deployment hygiene for a GenAI service.

## Release Process

Every release should include a versioned prompt or model configuration, evaluation report, rollback plan, and owner. Candidate changes should pass offline evaluation before beta exposure.

## Canary

Canary rollout sends a small percentage of traffic to a candidate version while monitoring latency, errors, refusal rate, retrieval hit rate, and evaluation pass rate. Roll forward only when quality and reliability remain within threshold.

## Rollback

Rollback should restore the previous application version, prompt configuration, and retrieval settings together. Recovery is confirmed by request success rate, latency, and representative evaluation checks.
