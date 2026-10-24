"""Durable intent, verified preservation, idempotent commit and undo recovery."""
from pathlib import Path
import uuid

from . import __version__
from .errors import IntegrityError, RecoverableFailure, UnsafeFilesystem
from .fs import (archive_name, available, backup_name, capacity, folder_lock,
                 hide, identity, move, now, relative_file, sha256, source_lease,
                 state_read, state_write)
from .history import History


class Transactions:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root / "runtime" / "state" / "transactions"

    def save(self, record, phase):
        record = dict(record, phase=phase, updated=now())
        state_write(self.directory / (record["transaction"] + ".json"), record)
        return record

    def pending(self):
        if not self.directory.exists():
            return []
        result = []
        for path in self.directory.glob("*.json"):
            data = state_read(path)
            if data["phase"] not in ("committed", "undone", "rolled_back", "backup_restored"):
                result.append(data)
        return result

    def commit(self, source, stage, original_hash, transaction, rules_hash, profile, trace):
        source, stage = Path(source), Path(stage)
        if stage.parent != source.parent or not stage.name.startswith(".icgf-" + transaction):
            raise IntegrityError("Staging ownership/location is invalid.")
        record = {"operation": "convert", "transaction": transaction, "folder": str(source.parent),
                  "original": source.name, "stage": stage.name, "original_hash": original_hash,
                  "corrected_hash": sha256(stage), "rules_fingerprint": rules_hash,
                  "profile": profile, "trace": trace, "program_version": __version__}
        capacity(source.parent, 65536)
        with folder_lock(source.parent), source_lease(source):
            if sha256(source) != original_hash:
                raise IntegrityError("Source changed after analysis/approval; commit refused.")
            history = History(source.parent)
            history.validate()
            reason, _ = history.recognize(original_hash)
            if reason in ("known_original", "known_corrected"):
                raise IntegrityError("Source became a known processed image before commit.")
            corrected = available(source.with_name(source.stem + "-gendeerfixed" + source.suffix))
            backup = available(backup_name(source))
            record.update(corrected=corrected.name, backup=backup.name,
                          original_attributes=getattr(source.stat(),"st_file_attributes",0),
                          original_size=source.stat().st_size, corrected_size=stage.stat().st_size)
            self.save(record, "prepared")
            committed = False
            try:
                move(source, backup)
                if sha256(backup) != original_hash:
                    raise IntegrityError("Preserved original did not verify.")
                self.save(record, "original_preserved")
                move(stage, corrected)
                hide(corrected,bool(record["original_attributes"] & 2))
                self.save(record, "output_published")
                event = history.append("committed", **self.event_values(record))
                committed = True
                try:
                    self.save(record, "committed")
                except OSError:
                    # Folder history is authoritative; startup reconciles this.
                    event = dict(event, warning="Local journal lagged; folder history committed.")
                return event
            except BaseException as error:
                if committed:
                    raise RecoverableFailure("Conversion committed; local bookkeeping needs reconciliation.") from error
                # An append may have reached disk before its flush reported an
                # error. Retain published files rather than rolling back a
                # transaction already visible in authoritative history.
                try:
                    written=History(source.parent).transactions().get(transaction)
                except IntegrityError:
                    written=None
                if written and written["event"] in ("committed","recovered"):
                    raise RecoverableFailure("History append outcome uncertain; files retained for recovery.") from error
                try:
                    if corrected.exists():
                        if sha256(corrected) != record["corrected_hash"] or stage.exists():
                            raise IntegrityError("Corrected path is ambiguous during rollback.")
                        move(corrected, stage)
                    if backup.exists():
                        if source.exists() or sha256(backup) != original_hash:
                            raise IntegrityError("Original path/backup is ambiguous during rollback.")
                        move(backup, source)
                    self.save(record, "rolled_back")
                except BaseException as rollback_error:
                    raise RecoverableFailure("Commit/rollback interrupted; originals retained. Run recover.") from rollback_error
                raise error

    @staticmethod
    def event_values(record):
        keys = ("transaction", "original", "corrected", "backup", "original_hash", "corrected_hash",
                "rules_fingerprint", "profile", "program_version", "original_size", "corrected_size")
        return {key: record[key] for key in keys if key in record}

    def undo(self, folder, event):
        folder = Path(folder)
        original = relative_file(folder, event["original"])
        corrected = relative_file(folder, event["corrected"])
        backup = relative_file(folder, event["backup"])
        with folder_lock(folder):
            active = History(folder).transactions().get(event["transaction"])
            if not active or active["event"] == "undone":
                raise IntegrityError("Transaction is no longer active.")
            if original.exists():
                raise UnsafeFilesystem("Original filename is occupied; no file was overwritten.")
            if not backup.is_file() or sha256(backup) != event["original_hash"]:
                raise IntegrityError("Original backup is missing or changed.")
            if not corrected.is_file():
                raise IntegrityError("Corrected file is missing; use explicit recovery.")
            archive = available(archive_name(corrected))
            with source_lease(corrected), source_lease(backup):
                archive_hash = sha256(corrected)
                record = dict(self.event_values(event), operation="undo", folder=str(folder),
                              archive=archive.name, archive_hash=archive_hash,
                              changed_corrected=archive_hash != event["corrected_hash"])
                self.save(record, "undo_prepared")
                try:
                    move(corrected, archive)
                    self.save(record, "undo_archived")
                    move(backup, original)
                    if sha256(original) != event["original_hash"]:
                        raise IntegrityError("Restored original failed verification.")
                    self.save(record, "undo_restored")
                except BaseException as error:
                    try:
                        if original.exists() and not backup.exists() and sha256(original) == event["original_hash"]:
                            move(original, backup)
                        if archive.exists() and not corrected.exists() and sha256(archive) == archive_hash:
                            move(archive, corrected)
                        self.save(record, "rolled_back")
                    except BaseException as rollback_error:
                        raise RecoverableFailure("Undo interrupted; retain all files and run recover.") from rollback_error
                    raise error
                try:
                    History(folder).append("undone", **self.event_values(record), archive=archive.name,
                                           archive_hash=archive_hash, changed_corrected=record["changed_corrected"])
                    self.save(record, "undone")
                except BaseException as error:
                    raise RecoverableFailure("Original restored, but undo history needs recovery.") from error
                return dict(record, restored=str(original), archive_path=str(archive))

    def recover(self):
        results = []
        for record in self.pending():
            folder = Path(record["folder"])
            if not folder.is_dir():
                raise RecoverableFailure("A pending transaction's folder moved; select/inspect it explicitly.")
            with folder_lock(folder):
                history = History(folder)
                history.validate()
                original = relative_file(folder, record["original"])
                corrected = relative_file(folder, record["corrected"])
                backup = relative_file(folder, record["backup"])
                known = history.transactions().get(record["transaction"])
                if record["operation"] == "convert":
                    if known and known["event"] in ("committed", "recovered", "undone"):
                        self.save(record, "undone" if known["event"] == "undone" else "committed")
                        results.append({"transaction": record["transaction"], "state": "history_reconciled"})
                        continue
                    stage = relative_file(folder, record["stage"])
                    if corrected.exists():
                        if sha256(corrected) != record["corrected_hash"] or stage.exists():
                            raise RecoverableFailure("Published output is ambiguous; no recovery files changed.")
                        move(corrected, stage)
                    if backup.exists():
                        if original.exists() or sha256(backup) != record["original_hash"]:
                            raise RecoverableFailure("Original/backup collision requires explicit recovery.")
                        move(backup, original)
                    if not original.exists() or sha256(original) != record["original_hash"]:
                        raise RecoverableFailure("Cannot establish a verified original after rollback.")
                    self.save(record, "rolled_back")
                elif record["operation"] == "undo":
                    archive = relative_file(folder, record["archive"])
                    if known and known["event"] == "undone":
                        self.save(record, "undone")
                    elif original.exists() and not backup.exists() and archive.exists():
                        if sha256(original) != record["original_hash"] or sha256(archive) != record["archive_hash"]:
                            raise RecoverableFailure("Undo recovery hash mismatch.")
                        history.append("undone", **self.event_values(record), archive=record["archive"],
                                       archive_hash=record["archive_hash"], changed_corrected=record["changed_corrected"])
                        self.save(record, "undone")
                    elif backup.exists() and not original.exists():
                        if archive.exists():
                            if corrected.exists() or sha256(archive) != record["archive_hash"]:
                                raise RecoverableFailure("Undo archive is ambiguous.")
                            move(archive, corrected)
                        if not corrected.exists() or sha256(backup) != record["original_hash"]:
                            raise RecoverableFailure("Cannot safely roll back undo.")
                        self.save(record, "rolled_back")
                    else:
                        raise RecoverableFailure("Undo state requires explicit inspection; files retained.")
                results.append({"transaction": record["transaction"], "state": "recovered"})
        return results
