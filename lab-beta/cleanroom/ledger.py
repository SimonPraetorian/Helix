"""Append-only, hash-chained evidence ledger with OS-backed writer serialization.

The chain is tamper-evident only when its head is anchored outside this file.
It is not a signature system or hardened, tamper-proof storage.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from contextlib import contextmanager


class LedgerError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


@contextmanager
def _exclusive_file_lock(stream):
    """Lock the ledger inode/handle; the OS releases ownership when a process exits."""
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class EvidenceLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.verify()

    def _read_unlocked(self, stream) -> list[dict[str, Any]]:
        stream.seek(0)
        raw = stream.read()
        if raw and not raw.endswith(b"\n"):
            raise LedgerError("ledger has an incomplete final record")
        rows = []
        previous = "0" * 64
        for number, line in enumerate(raw.splitlines(), 1):
            try:
                row = json.loads(line)
                supplied = row.pop("hash")
                if row.get("sequence") != number or row.get("previous_hash") != previous:
                    raise LedgerError(f"sequence or chain mismatch at record {number}")
                expected = hashlib.sha256(bytes.fromhex(previous) + canonical(row)).hexdigest()
                if supplied != expected:
                    raise LedgerError(f"hash mismatch at record {number}")
                row["hash"] = supplied
                rows.append(row)
                previous = supplied
            except LedgerError:
                raise
            except Exception as exc:
                raise LedgerError(f"invalid record {number}: {exc}") from exc
        return rows

    def verify(self) -> dict[str, Any]:
        with self.path.open("a+b") as stream:
            with _exclusive_file_lock(stream):
                rows = self._read_unlocked(stream)
        return {"valid": True, "records": len(rows), "head": rows[-1]["hash"] if rows else "0" * 64}

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.path.open("a+b") as stream:
            with _exclusive_file_lock(stream):
                rows = self._read_unlocked(stream)
                previous = rows[-1]["hash"] if rows else "0" * 64
                body = {"sequence": len(rows) + 1, "previous_hash": previous, "event": event, "payload": payload}
                digest = hashlib.sha256(bytes.fromhex(previous) + canonical(body)).hexdigest()
                record = dict(body, hash=digest)
                stream.seek(0, os.SEEK_END)
                stream.write(canonical(record) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
                return record

    def records(self) -> list[dict[str, Any]]:
        with self.path.open("a+b") as stream:
            with _exclusive_file_lock(stream):
                return self._read_unlocked(stream)
