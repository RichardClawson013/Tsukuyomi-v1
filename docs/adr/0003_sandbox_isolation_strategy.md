# ADR 0003: Git-Worktree Sandbox for v1.0; Microsandbox Migration in v1.1

| Field | Value |
| --- | --- |
| **Status** | Accepted (v1.0); migration scheduled for v1.1 |
| **Date** | 2026-04-19 |
| **Decision-makers** | Rob de Vet |
| **Consulted** | Microsandbox project (`zerocore-ai/microsandbox`), Penligent four-boundary research |

## Context

The Infinite Tsukuyomi sandbox (Section 5 of `docs/research/PAPER.md`) executes proposed plans in a simulated environment before allowing real execution. Required isolation properties:

1. Filesystem changes must not leak to the real filesystem.
2. Network egress must be blocked or controlled.
3. Resource consumption (CPU, memory, time) must be capped.
4. Cleanup must be reliable; "leaked" sandboxes must not accumulate.

Available isolation primitives, ranked by strength:

- **No isolation** — just `cwd` change. Trivially escapable. Unacceptable.
- **Git worktree + path validation** — filesystem isolation per worktree; programmatic enforcement of "stay inside the worktree." No network or process isolation.
- **chroot/`unshare`** — Linux namespaces; stronger but kernel-shared.
- **Container (Docker, Podman)** — process isolation, network isolation, but kernel-shared. Subject to container-escape CVEs.
- **microVM (Firecracker, libkrun, Krunkit, Microsandbox)** — separate kernel, full isolation. Sub-100ms boot in modern implementations.

## Decision

**v1.0 ships with a hardened git-worktree sandbox.** A separate `WorktreeSandboxBackend` class implements the interface; a `MicrosandboxBackend` will land in v1.1 implementing the same interface and becoming the default.

The hardened worktree applies four layers (`docs/research/PAPER.md` §5.3): path validation, process limits (ulimit), kernel namespaces (where available, opportunistic), and HTTP proxy black-holing.

## Rationale

### Why not microVM in v1.0

1. **Microsandbox is young.** As of April 2026, Microsandbox v0.x is functional but the API is still stabilizing. Building a v1.0 release on a v0.x dependency creates upgrade risk.
2. **Platform coverage.** Microsandbox requires `/dev/kvm` on Linux (and equivalent on macOS via Hypervisor.framework). Many developer workstations have it (the author's WSL2 setup does, as confirmed); some do not, especially nested-virtualization environments and some CI runners.
3. **v1.0 ships now; v1.1 ships in 6 months.** Worktree-with-hardening is sufficient for the primary v1.0 use case (single trusted user, trusted codebase) and unblocks shipping. Microsandbox migration is a known-finite project for v1.1.

### Why not Docker

Docker is container-isolation, not VM-isolation. On a kernel-shared model, container escapes are a recurring (low-frequency, high-impact) class of CVE. For a *safety* product, the upgrade from "filesystem isolation" to "container isolation" is real but small; the upgrade to "true VM isolation" is the meaningful one.

Additionally, Docker on Linux hosts (including WSL2) imposes daemon dependencies and cgroup configuration that increase operational complexity.

### Why hardened worktree is acceptable for v1.0

The threat model for v1.0 is:
- **In scope**: agent makes a mistake; agent gets injected with hostile input from a doc/web search; agent's plan would damage the host filesystem if executed; agent enters a runaway loop.
- **Out of scope (v1.0)**: kernel-CVE exploitation by adversarial agent (single-trusted-user deployment); cross-tenant attacks (no multi-tenancy in v1.0); deliberate sandbox-escape attempts (assumes a sufficiently sophisticated adversary, which is not the v1.0 user).

For the v1.0 threat model, a worktree with the four hardening layers is sufficient: filesystem changes go to a separate worktree directory, paths outside that directory are programmatically refused, network egress is black-holed, and process limits cap runaway resource consumption. We document the limitation explicitly; we don't pretend this is microVM.

### Why microVM in v1.1

For multi-tenant deployments, untrusted-code execution (which Tsukuyomi may eventually be asked to mediate), or hardened production scenarios, microVM isolation is the correct model. Microsandbox is the right project to standardize on (Apache-2.0, libkrun-based, Python SDK).

## Consequences

### v1.0 (worktree)

**Positive**: zero new dependencies, fast, predictable, works everywhere git works.

**Negative**: kernel-shared; not safe against motivated adversaries; documented limitation.

### v1.1 (Microsandbox)

**Positive**: real VM isolation; safe against kernel-share threats; sub-100ms boot.

**Negative**: requires `/dev/kvm` (Linux) or Hypervisor.framework (macOS); fall-back path needed for environments without virtualization.

## Compliance

PRs that introduce a new sandbox backend must implement the `SandboxBackend` interface in `src/tsukuyomi/organs/sandbox/base.py` and add corresponding `tests/integration/test_sandbox_<backend>.py`. PRs that bypass the sandbox interface to provide direct execution paths are forbidden.
