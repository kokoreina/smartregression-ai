"""Atomic, fail-closed local session reservations; OS lock survives process crashes."""

import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path


class BudgetLedger:
    def __init__(self, path: Path, *, session_id: str) -> None:
        self.path = path
        if not session_id or len(session_id) > 128:
            raise ValueError("invalid_budget_session")
        self.session_id = session_id
        self._state = None
        self._run = None
        self._cap = 0

    def read(self) -> dict:
        if self.path.is_symlink() or self.path.is_junction():
            raise ValueError("unsafe_budget_path")
        if not self.path.exists():
            return dict(version=1, session=self.session_id, runs=[])
        if self.path.stat().st_size > 1_000_000:
            raise ValueError("invalid_budget_ledger")
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or set(value) != {"version", "session", "runs"}
            or value["version"] != 1
            or value["session"] != self.session_id
            or not isinstance(value["runs"], list)
            or len(value["runs"]) > 5
        ):
            raise ValueError("invalid_budget_ledger")
        ids = []
        for run in value["runs"]:
            if (
                not isinstance(run, dict)
                or set(run) != {"id", "config", "entries"}
                or not isinstance(run["id"], str)
                or not 0 < len(run["id"]) <= 128
                or not isinstance(run["config"], str)
                or len(run["config"]) != 64
                or not isinstance(run["entries"], list)
            ):
                raise ValueError("invalid_budget_ledger")
            ids.append(run["id"])
            if len(run["entries"]) > 3:
                raise ValueError("invalid_budget_ledger")
            for entry in run["entries"]:
                if (
                    not isinstance(entry, dict)
                    or set(entry)
                    != {
                        "kind",
                        "reserved_micro_usd",
                        "charged_micro_usd",
                        "actual_micro_usd",
                        "state",
                    }
                    or entry["kind"] not in {"count", "generation"}
                    or any(
                        type(entry[k]) is not int or not 0 <= entry[k] <= 20000
                        for k in ("reserved_micro_usd", "charged_micro_usd")
                    )
                    or entry["charged_micro_usd"] > entry["reserved_micro_usd"]
                    or entry["state"] not in {"unknown", "observed"}
                    or (
                        entry["actual_micro_usd"] is not None
                        and (
                            type(entry["actual_micro_usd"]) is not int
                            or entry["actual_micro_usd"] != entry["charged_micro_usd"]
                        )
                    )
                    or ((entry["state"] == "observed") != (entry["actual_micro_usd"] is not None))
                ):
                    raise ValueError("invalid_budget_ledger")
            if sum(e["charged_micro_usd"] for e in run["entries"]) > 20000:
                raise ValueError("invalid_budget_ledger")
        if len(set(ids)) != len(ids) or self._spent(value) > 100000:
            raise ValueError("invalid_budget_ledger")
        return value

    @staticmethod
    def _spent(state: dict) -> int:
        return sum(e["charged_micro_usd"] for run in state["runs"] for e in run["entries"])

    def _save(self) -> None:
        temporary = self.path.with_name(self.path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                json.dump(self._state, stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    @contextmanager
    def open_run(self, run_id: str, config: str, cap: int):
        if any(p.is_symlink() or p.is_junction() for p in (self.path, *self.path.parents)):
            raise ValueError("unsafe_budget_path")
        if type(cap) is not int or not 0 < cap <= 20000:
            raise ValueError("invalid_run_budget")
        lock = self.path.with_name(self.path.name + ".lock")
        if lock.is_symlink() or lock.is_junction():
            raise ValueError("unsafe_budget_path")
        handle = lock.open("a+b")
        acquired = False
        try:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
            self._state = self.read()
            if len(self._state["runs"]) >= 5 or any(r["id"] == run_id for r in self._state["runs"]):
                raise ValueError("provider_budget")
            self._run = dict(id=run_id, config=config, entries=[])
            self._cap = cap
            self._state["runs"].append(self._run)
            self._save()
            yield self
        finally:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
            if acquired:
                self._state = None
                self._run = None

    def reserve(self, kind: str, amount: int) -> int:
        if (
            self._run is None
            or kind not in {"count", "generation"}
            or type(amount) is not int
            or amount < 0
        ):
            raise ValueError("invalid_reservation")
        entries = self._run["entries"]
        if (
            (kind == "count" and entries)
            or (kind == "generation" and not entries)
            or len(entries) >= 3
            or sum(e["charged_micro_usd"] for e in entries) + amount > self._cap
            or self._spent(self._state) + amount > 100000
        ):
            raise ValueError("provider_budget")
        entries.append(
            dict(
                kind=kind,
                reserved_micro_usd=amount,
                charged_micro_usd=amount,
                actual_micro_usd=None,
                state="unknown",
            )
        )
        self._save()
        return len(entries) - 1

    def settle(self, entry: int, amount: int | None) -> None:
        value = self._run["entries"][entry]
        if amount is not None:
            if type(amount) is not int or not 0 <= amount <= value["reserved_micro_usd"]:
                raise ValueError("provider_budget")
            value["charged_micro_usd"] = amount
            value["actual_micro_usd"] = amount
            value["state"] = "observed"
        self._save()
