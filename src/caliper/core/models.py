from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

RunStatus = Literal["running", "awaiting_approval", "paused", "done", "failed"]
StepStatus = Literal["started", "committed", "unknown", "skipped"]


@dataclass(frozen=True)
class Budget:
    max_steps: int = 40
    max_tokens: int = 200_000
    max_wall_s: int = 600
    max_usd: float = 0.50


@dataclass
class RunRequest:
    task_id: str
    prompt: str
    budget: Budget = field(default_factory=Budget)


@dataclass
class Run:
    id: str
    task_id: str
    status: RunStatus
    created_at: str
    budget: Budget


@dataclass
class Step:
    run_id: str
    seq: int
    kind: str
    idempotency_key: str
    status: StepStatus
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Checkpoint:
    run_id: str
    seq: int
    state: dict[str, Any]
    created_at: str


@dataclass
class Approval:
    id: str
    run_id: str
    step_seq: int
    tool: str
    args_digest: str
    decision: Literal["pending", "approved", "denied"]
    note: str = ""


@dataclass
class RunResult:
    run_id: str
    ok: bool
    wall_s: float
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    artifact_dir: Path | None = None
    failure: str | None = None
