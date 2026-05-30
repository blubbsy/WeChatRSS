# Modernization Plan

This plan focuses on improving stability, performance, and maintainability without changing the external behavior of WeChatRSS.

## Phase 1: Runtime Separation

- Move scheduler lifecycle ownership out of the FastAPI request layer.
- Keep the web app responsible for HTTP, auth, and rendering only.
- Give the scraper worker a single place to start, stop, and restart jobs.

## Phase 2: Scraper Isolation

- Split long-running scraping work from request-triggered code paths.
- Reduce coupling between discovery, extraction, storage, and RSS generation.
- Make per-account syncs explicit instead of launching full-cycle scrapes from generic handlers.

## Phase 3: I/O and Throughput

- Replace blocking network calls inside async code.
- Reuse browser resources where safe instead of launching new contexts for every action.
- Add lightweight backoff and retry policies around transient failures.

## Phase 4: Data and Packaging

- Add indexes and explicit migration helpers for the hottest SQLite paths.
- Remove path mutation bootstrapping and converge on package-safe imports.
- Add narrow tests around auth, scheduler behavior, and feed generation.

## Initial Success Criteria

- The API server can start and stop without owning job control state directly.
- Restarting settings no longer risks duplicating scheduler instances.
- The scheduler lifecycle is testable in isolation.