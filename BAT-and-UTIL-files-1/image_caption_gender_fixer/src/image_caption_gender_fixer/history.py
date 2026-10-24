"""Authoritative folder-relative, hidden, append-only transaction history."""
import hashlib
import json
from pathlib import Path
import os
import uuid

from .errors import IntegrityError
from .fs import canonical, hide, now, relative_file, reparse


class History:
    filename = ".history.icgf"

    def __init__(self, folder):
        self.folder = Path(folder)
        self.path = self.folder / self.filename
        self.records = []
        self.tail_error = None
        if self.path.exists():
            if reparse(self.path):
                raise IntegrityError("History is a reparse point; refused.")
            self._read()

    def _read(self):
        previous = "0" * 64
        seen = set()
        raw_lines = self.path.read_bytes().splitlines(keepends=True)
        for index, raw in enumerate(raw_lines):
            try:
                if not raw.endswith(b"\n"):
                    raise ValueError("incomplete final write")
                record = json.loads(raw.decode("utf-8"))
                if not isinstance(record,dict):
                    raise ValueError("history record must be an object")
                checksum = record.pop("checksum")
                if record.get("application") != "icgf" or record.get("schema") != 1:
                    raise ValueError("unsupported history application/schema")
                if record.get("seq") != index or record.get("previous") != previous:
                    raise ValueError("history sequence/hash chain mismatch")
                if hashlib.sha256(canonical(record).encode()).hexdigest() != checksum:
                    raise ValueError("history checksum mismatch")
                if record.get("event_id") in seen:
                    raise ValueError("duplicated event ID")
                seen.add(record["event_id"])
                if index == 0 and record.get("event") != "header":
                    raise ValueError("missing history header")
                if index > 0:
                    if record.get("event") not in ("committed", "undone", "recovered"):
                        raise ValueError("unknown history event")
                    uuid.UUID(record["transaction"])
                    for key in ("original", "corrected", "backup", "archive"):
                        if record.get(key):
                            relative_file(self.folder, record[key])
                    for key in ("original_hash", "corrected_hash"):
                        if len(record.get(key, "")) != 64 or any(c not in "0123456789abcdef" for c in record[key]):
                            raise ValueError("invalid content hash")
                record["checksum"] = checksum
                self.records.append(record)
                previous = checksum
            except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
                self.tail_error = f"History record {index + 1}: {error}. Readable prefix retained; mutation refused."
                break
        if not raw_lines:
            self.tail_error = "Empty/unrecognized history; file retained."

    def validate(self):
        if self.tail_error:
            raise IntegrityError(self.tail_error)

    def append(self, event, **values):
        """Caller must hold the folder lock. Re-read to avoid stale append state."""
        fresh = History(self.folder)
        fresh.validate()
        self.records = fresh.records
        if not self.path.exists():
            self._append("header", history_id=str(uuid.uuid4()))
        hide(self.path)
        for record in self.records:
            if event != "header" and record.get("transaction") == values.get("transaction") and record["event"] == event:
                for key, value in values.items():
                    if record.get(key) != value:
                        raise IntegrityError("Idempotent event disagrees with committed history.")
                return record
        return self._append(event, **values)

    def _append(self, event, **values):
        record = dict(values, application="icgf", schema=1, seq=len(self.records),
                      previous=self.records[-1]["checksum"] if self.records else "0" * 64,
                      event=event, event_id=str(uuid.uuid4()), timestamp=now())
        record["checksum"] = hashlib.sha256(canonical(record).encode()).hexdigest()
        mode = "ab" if self.path.exists() else "xb"
        with self.path.open(mode) as handle:
            handle.write((canonical(record) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        self.records.append(record)
        return record

    def transactions(self):
        result = {}
        for record in self.records:
            if record.get("transaction"):
                previous = result.get(record["transaction"])
                if previous and record["event"] in ("committed","recovered"):
                    raise IntegrityError("Repeated conversion event for one transaction.")
                if record["event"] == "undone" and (not previous or previous["event"] == "undone"):
                    raise IntegrityError("Undo event has no active conversion.")
                result[record["transaction"]] = record
        return result

    def recognize(self, digest):
        self.validate()
        states = self.transactions()
        corrected = [r for r in self.records if r.get("corrected_hash") == digest]
        if corrected:
            return "known_corrected", corrected[-1]
        originals = [r for r in states.values() if r.get("original_hash") == digest]
        if originals:
            active = next((r for r in originals if r["event"] != "undone"), None)
            return ("known_original", active) if active else ("previously_undone", originals[-1])
        return None, None

    def resolve(self, name):
        self.validate()
        return [r for r in self.transactions().values() if r["event"] != "undone" and
                (name == r.get("transaction") or name in (r.get("original"), r.get("corrected"), r.get("backup")))]
