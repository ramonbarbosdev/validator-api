"""Fila e status da validacao de PR (webhook / runner)."""
from __future__ import annotations

import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

_MAX_RECENT = 25


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueueJob:
    pr_number: int
    enqueued_at: str
    event: str
    reason: str
    head_sha: str | None = None
    force: bool = False


@dataclass
class FinishedJob:
    pr_number: int
    enqueued_at: str
    finished_at: str
    duration_sec: float
    exit_code: int
    error: str | None = None


class ValidationQueue:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: deque[QueueJob] = deque()
        self._current: QueueJob | None = None
        self._phase: str = "idle"
        self._phase_since: str | None = None
        self._recent: deque[FinishedJob] = deque(maxlen=_MAX_RECENT)
        self._worker_started = False
        self._run_fn: Callable[[int, bool], int] | None = None

    def _log(self, msg: str) -> None:
        print(f"[queue] {msg}", flush=True)

    def set_phase(self, phase: str, pr_number: int | None = None) -> None:
        with self._lock:
            self._phase = phase
            self._phase_since = _utc_now()
            cur = self._current.pr_number if self._current else pr_number
        if cur is not None:
            self._log(f"PR #{cur} — {phase}")

    def enqueue(
        self,
        job: QueueJob,
        *,
        dedupe_pending: bool = True,
    ) -> tuple[int, int]:
        with self._lock:
            if dedupe_pending:
                self._pending = deque(j for j in self._pending if j.pr_number != job.pr_number)
            self._pending.append(job)
            pending_n = len(self._pending)
            position = pending_n + (1 if self._current else 0)
        self._log(
            f"PR #{job.pr_number} enfileirada "
            f"(posicao ~{position}, evento={job.event}, {job.reason})"
        )
        return position, pending_n

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            current = None
            if self._current:
                current = {
                    "pr": self._current.pr_number,
                    "since": self._current.enqueued_at,
                    "event": self._current.event,
                    "reason": self._current.reason,
                    "head_sha": self._current.head_sha,
                    "phase": self._phase,
                    "phase_since": self._phase_since,
                }
            pending = [
                {
                    "pr": j.pr_number,
                    "enqueued_at": j.enqueued_at,
                    "event": j.event,
                    "reason": j.reason,
                    "head_sha": j.head_sha,
                }
                for j in list(self._pending)
            ]
            recent = [
                {
                    "pr": f.pr_number,
                    "finished_at": f.finished_at,
                    "duration_sec": round(f.duration_sec, 1),
                    "exit_code": f.exit_code,
                    "error": f.error,
                }
                for f in list(self._recent)
            ]
            return {
                "current": current,
                "pending": pending,
                "pending_count": len(pending),
                "recent": recent,
            }

    def start_worker(self, run_fn: Callable[[int, bool], int]) -> None:
        with self._lock:
            if self._worker_started:
                return
            self._worker_started = True
            self._run_fn = run_fn

        def loop() -> None:
            while True:
                job = self._take_next()
                if job is None:
                    time.sleep(0.25)
                    continue
                t0 = time.monotonic()
                err: str | None = None
                rc = 1
                self.set_phase("iniciando", job.pr_number)
                try:
                    if self._run_fn is None:
                        raise RuntimeError("worker sem run_fn")
                    rc = self._run_fn(job.pr_number, job.force)
                except Exception as e:
                    err = str(e)
                    self._log(f"PR #{job.pr_number} erro: {e}")
                    print(f"[queue] PR #{job.pr_number} erro: {e}", file=sys.stderr, flush=True)
                finally:
                    dur = time.monotonic() - t0
                    finished = FinishedJob(
                        pr_number=job.pr_number,
                        enqueued_at=job.enqueued_at,
                        finished_at=_utc_now(),
                        duration_sec=dur,
                        exit_code=rc,
                        error=err,
                    )
                    with self._lock:
                        self._recent.append(finished)
                        self._current = None
                        self._phase = "idle"
                        self._phase_since = _utc_now()
                    status = "ok" if rc == 0 else f"exit {rc}"
                    self._log(f"PR #{job.pr_number} concluida ({status}, {dur:.0f}s)")

        threading.Thread(target=loop, name="validator-api-worker", daemon=True).start()

    def _take_next(self) -> QueueJob | None:
        with self._lock:
            if self._current is not None or not self._pending:
                return None
            job = self._pending.popleft()
            self._current = job
            rest = len(self._pending)
        self._log(f"PR #{job.pr_number} iniciando validacao ({rest} na fila)")
        return job


_QUEUE = ValidationQueue()


def get_queue() -> ValidationQueue:
    return _QUEUE
