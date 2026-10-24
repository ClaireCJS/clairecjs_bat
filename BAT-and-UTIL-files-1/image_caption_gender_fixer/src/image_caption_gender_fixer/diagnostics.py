"""Local, text-free operation logs and read-only bundle diagnostics."""
import json
import os
from pathlib import Path
import traceback
import uuid

from . import __version__
from .fs import now, sha256, validate_path
from .errors import ICGFError

SCHEMAS={"program":__version__,"rules":1,"metadata_marker":1,"folder_history":1,
         "sessions":1,"transactions":1,"preferences":1,"bundle":1}


class Audit:
    def __init__(self, root, command):
        self.root=Path(root)
        self.run=str(uuid.uuid4())
        self.path=self.root/"runtime/logs"/(self.run+".jsonl")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open("x",encoding="utf-8",newline="\n")
        self.record("started",command=command)

    def record(self,event,**values):
        # Only these non-content fields can enter the log. No OCR, rule text,
        # filenames, user paths, exception strings, or traceback locals.
        allowed={k:v for k,v in values.items() if k in ("command","code","session","transaction","exception_type","states")}
        self.stream.write(json.dumps(dict(application="icgf",schema=1,program=__version__,time=now(),run=self.run,event=event,**allowed))+"\n")
        self.stream.flush();os.fsync(self.stream.fileno())

    def crash(self,error):
        path=self.root/"runtime/crash-reports"/(self.run+".json")
        path.parent.mkdir(parents=True,exist_ok=True)
        frames=[{"module":Path(frame.filename).name,"line":frame.lineno,"function":frame.name}
                for frame in traceback.extract_tb(error.__traceback__)]
        data={"application":"icgf","schema":1,"time":now(),"run":self.run,
              "exception_type":type(error).__name__,"frames":frames}
        with path.open("x",encoding="utf-8") as output:
            json.dump(data,output);output.flush();os.fsync(output.fileno())
        return path

    def close(self):
        self.stream.close()


def bundle_health(root):
    root=Path(root)
    result={"checked":0,"optional_absent":[],"errors":[]}
    try:
        manifest=json.loads((root/"environment/manifest.json").read_text(encoding="utf-8"))
        if manifest.get("application")!="icgf" or manifest.get("schema")!=1:
            raise ValueError("Unsupported bundle manifest")
        if not isinstance(manifest.get("files"),dict) or not isinstance(manifest.get("optional_files",[]),list):
            raise ValueError("Malformed manifest member/optional file lists")
        from .maintenance import package_directory
        packages=package_directory(root)
        optional=set(manifest.get("optional_files",[]))
        for relative,expected in manifest["files"].items():
            candidate=Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts or ":" in relative or "\\" in relative:
                raise ValueError("Unsafe manifest path")
            path=root/"environment"/candidate
            if candidate.parts and candidate.parts[0]=="packages":
                path=packages/Path(*candidate.parts[1:])
            if not path.exists() and relative in optional:
                result["optional_absent"].append(relative);continue
            try:
                validate_path(path)
                if not path.is_file() or path.stat().st_size!=expected["size"] or sha256(path)!=expected["sha256"]:
                    result["errors"].append({"file":relative,"issue":"Missing or hash/size mismatch"})
                result["checked"]+=1
            except (OSError,ValueError,ICGFError) as error:
                result["errors"].append({"file":relative,"issue":type(error).__name__})
    except (OSError,ValueError,KeyError,TypeError,ICGFError) as error:
        result["errors"].append({"file":"manifest.json","issue":type(error).__name__})
    return result
