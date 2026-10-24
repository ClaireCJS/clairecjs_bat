from pathlib import Path
import uuid

from .errors import IntegrityError, RecoverableFailure
from .fs import now, recycle, sha256, identity, state_read, state_write, reparse

RESUMABLE=("pending","deferred","failed","interrupted","canceled")
STATES=RESUMABLE+("committed","skipped")


class Sessions:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root / "runtime" / "state" / "sessions"
        self.issues=[]

    @staticmethod
    def validate(session,filename=None):
        if not isinstance(session,dict) or not isinstance(session.get("items"),list) or not all(isinstance(session.get(k),str) for k in ("profile","id","created","updated")):
            raise IntegrityError("Malformed session journal.")
        if str(uuid.UUID(session["id"]))!=session["id"] or filename and filename!=session["id"]+".json":
            raise IntegrityError("Session identity does not match its filename.")
        for item in session["items"]:
            if not isinstance(item,dict) or item.get("state") not in STATES or not isinstance(item.get("path"),str) or not Path(item["path"]).is_absolute():
                raise IntegrityError("Malformed session item.")
            digest=item.get("hash","")
            if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
                raise IntegrityError("Invalid session source hash.")
        return session

    def list(self):
        self.issues=[]
        if not self.directory.exists():
            return []
        result=[]
        for path in sorted(self.directory.glob("*.json")):
            if path.name.startswith(".icgf-state-"): continue
            try:
                if reparse(path): raise IntegrityError("Session is a reparse point.")
                result.append(self.validate(state_read(path),path.name))
            except (OSError,ValueError,TypeError,KeyError,IntegrityError) as error:
                self.issues.append({"journal":path.name,"issue":str(error)})
        return result

    def unfinished(self):
        return [s for s in self.list() if any(i["state"] in RESUMABLE for i in s["items"])]

    def load(self, session_id):
        try: valid=str(uuid.UUID(session_id))==session_id
        except (ValueError,TypeError,AttributeError): valid=False
        if not valid:
            raise IntegrityError("Invalid session ID.")
        result = state_read(self.directory / (session_id + ".json"))
        if result is None:
            raise IntegrityError("Unknown session.")
        return self.validate(result,session_id+".json")

    def save(self, session):
        self.validate(session)
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
                "remaining": sum(counts.get(k, 0) for k in RESUMABLE)}

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
