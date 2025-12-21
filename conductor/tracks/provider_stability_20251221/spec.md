# Specification: Improve AI Provider Stability

## Overview
Webscout relies on many reverse-engineered AI providers. These endpoints are prone to changes, rate-limiting, or being taken offline. This track aims to implement a health-check system that can programmatically verify the status of these providers.

## Goals
- Automate the detection of broken AI provider endpoints.
- Provide a standardized way for any provider to be "pinged" for health status.
- Generate reports (JSON/Markdown) on provider availability.
- Reduce the manual effort required to maintain the provider list.

## Requirements
- **Standardized Health Check Interface:** Define a method (e.g., `check_health()`) that can be implemented by provider classes.
- **Centralized Health Runner:** A utility that iterates through registered providers and executes their health checks.
- **Async Execution:** Health checks should run concurrently to minimize total execution time.
- **Graceful Failure Handling:** The system should handle timeouts and network errors without crashing.
- **CLI Integration:** Add a `webscout health` command to trigger the checks manually.

## Out of Scope
- Automatically fixing broken providers (this requires manual reverse engineering).
- Performance benchmarking of every provider (focus is on availability first).
