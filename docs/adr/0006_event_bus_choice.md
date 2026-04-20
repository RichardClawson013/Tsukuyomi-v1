# ADR 0006: asyncio.Queue as the v1.0 Event Bus; ZeroMQ Reserved for v1.2 Multi-Process

| Field | Value |
| --- | --- |
| **Status** | Accepted (v1.0); revisit when multi-agent parallelism lands |
| **Date** | 2026-04-19 |

## Context

Organs and protocols communicate via signals (the interaction matrix in `docs/architecture/03_organs.md` §4.9). The implementation choice for the signaling mechanism affects performance, observability, and what topology becomes possible.

Options:

- **Direct method calls** with shared state. Simplest. No introspection of "who signaled whom."
- **In-process pub/sub** via `asyncio.Queue` or similar. Decoupled, observable, single-process.
- **ZeroMQ** for cross-process or cross-host messaging. Heavier; supports topologies Tsukuyomi v1.0 does not need.
- **Redis pub/sub.** External dependency.

## Decision

**`asyncio.Queue` based pub/sub for v1.0**, behind an interface (`NerveCore.publish` / `NerveCore.subscribe`) that can be swapped for ZeroMQ in v1.2 without organ-side code changes.

## Rationale

v1.0 is single-process, single-instance. Cross-process or cross-host messaging is unused. Adding ZeroMQ now would impose dependency weight (the `pyzmq` build dependency) for capability we do not exercise.

The interface-first approach (`NerveCore` is a Protocol, with one current implementation `AsyncioNerveCore`) keeps the upgrade path open. v1.2 multi-agent orchestration will be the trigger to add `ZmqNerveCore`.

## Consequences

**Positive**: zero extra dependencies; observable through standard asyncio profiling; trivial debugging.

**Negative**: doesn't scale to multi-process — but it doesn't need to in v1.0.

## Compliance

Organs MUST publish/subscribe via `NerveCore`, not directly to other organs. PRs that import organ A from organ B for direct method calls are rejected; the bus is the integration surface.
