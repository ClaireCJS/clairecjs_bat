from pathlib import Path
import uuid

from .errors import IntegrityError, RecoverableFailure
from .fs import now, recycle, sha256, identity, state_read, state_write


class Sessions:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root / "runtime" / "state" / "sessions"

    def list(self):
        if not self.directory.exists():
            return []
        return [state_read(p) for p in sorted(self.directory.glob("*.json"))]

    def unfinished(self):
        return [s for s in self.list() if any(i["state"] in ("pending", "deferred", "failed", "interrupted") for i in s["items"])]

    def load(self, session_id):
        if str(uuid.UUID(session_id)) != session_id:
            raise IntegrityError("Invalid session ID.")
        result = state_read(self.directory / (session_id + ".json"))
        if result is None:
            raise IntegrityError("Unknown session.")
        return result

    def save(self, session):
        session["updated"] = now()
        state_write(self.directory / (session["id"] + ".json"), session)

    def create(self, paths, profile):
        session = {"id": str(uuid.uuid4()), "created": now(), "updated": now(), "profile": profile,
                   "items": [{"path": str(p), "hash": sha256(p), "state": "pending", "artifacts": []} for p in paths]}
        self.save(session)
        return session

    @staticmethod
    def summary(session):
        counts = {}
        for item in session["items"]:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        return {"id": session["id"], "created": session["created"], "updated": session["updated"],
                "target": session["items"][0]["path"] if session["items"] else None, "counts": counts,
                "completed": counts.get("committed", 0), "failed": counts.get("failed", 0),
                "remaining": sum(counts.get(k, 0) for k in ("pending", "deferred", "failed", "interrupted"))}

    def abandon(self, session, pending_transactions):
        ids = {item.get("transaction") for item in session["items"]}
        if any(p["transaction"] in ids for p in pending_transactions):
            raise RecoverableFailure("Recover this session's interrupted image transaction before abandoning it.")
        for item in session["items"]:
            for artifact in item.get("artifacts", [])+item.get("retained_artifacts",[]):
                path = Path(artifact["path"])
                if path.exists():
                    if path.parent != Path(item["path"]).parent or not path.name.startswith(".icgf-") or not artifact.get("identity") or identity(path)[:2] != artifact["identity"] or sha256(path) != artifact["hash"]:
                        raise IntegrityError("Artifact changed; retain session and inspect it.")
                    recycle(path)
        recycle(self.directory / (session["id"] + ".json"))
