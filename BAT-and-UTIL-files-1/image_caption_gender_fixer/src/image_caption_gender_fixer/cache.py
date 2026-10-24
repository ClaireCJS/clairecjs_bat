"""Disposable cross-folder lookup cache, derived only from observed histories."""
from pathlib import Path
from .fs import state_read,state_write
from .history import History


class HashCache:
    def __init__(self,root):
        self.path=Path(root)/"runtime/cache/hash-index.json"
        self.warning=None
        try:
            self.data=state_read(self.path,{"histories":{}})
            if not isinstance(self.data.get("histories"),dict): raise ValueError("invalid derived cache")
        except (OSError,ValueError,KeyError,TypeError) as error:
            self.data={"histories":{}}
            self.warning="Derived hash cache unavailable; folder history remains authoritative. "+str(error)

    def observe(self,history):
        if self.warning or not history.records or history.tail_error:
            return
        history_id=history.records[0]["history_id"]
        entry={"folder":str(history.folder),"checksum":history.records[-1]["checksum"],
               "corrected":sorted({r["corrected_hash"] for r in history.records if r.get("corrected_hash")}),
               "active_originals":{r["original_hash"]:r["transaction"] for r in history.transactions().values() if r["event"]!="undone"}}
        if self.data["histories"].get(history_id)==entry:
            return
        self.data["histories"][history_id]=entry
        state_write(self.path,self.data)

    def recognize(self,digest):
        for entry in self.data["histories"].values():
            if digest in entry.get("corrected",[]):
                return "known_corrected_cross_folder"
            transaction=entry.get("active_originals",{}).get(digest)
            folder=Path(entry["folder"])
            if transaction and (folder/History.filename).is_file():
                try:
                    history=History(folder);history.validate()
                    record=history.transactions().get(transaction)
                    if record and record["event"]!="undone" and record["original_hash"]==digest:
                        return "known_original_cross_folder"
                except (OSError,ValueError):
                    continue
        return None
