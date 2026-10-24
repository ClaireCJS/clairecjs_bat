"""Terminal review, administrative commands and stable automation results."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import glob
import fnmatch
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from . import __version__
from .errors import ICGFError, IntegrityError, SelectionRequired, DependencyUnavailable, UnsafeFilesystem, Cancelled, ImageDeferred
from .fs import (available, canonical, folder_lock, identity, now, recycle, reparse,
                 sha256, state_read, state_write, validate_path, is_network)
from .history import History
from .rules import Rule, RuleStore, builtins, fingerprint, transform
from .sessions import Sessions
from .transactions import Transactions
from .cache import HashCache
from . import dependencies


class ArgumentsError(ICGFError):
    code = 64


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentsError(message)

    def parse_intermixed_args(self,args=None,namespace=None):
        args=list(sys.argv[1:] if args is None else args)
        if "--" in args:
            end=args.index("--")
            parsed=super().parse_intermixed_args(args[:end],namespace)
            parsed.items.extend(args[end+1:])
            return parsed
        return super().parse_intermixed_args(args,namespace)


def product_name(path):
    path=Path(path);name=path.name.casefold()
    return name.startswith((".icgf-",".history.icgf",".image-gender-fixer")) or bool(re.search(r"\.bak\.\d{12}\.(?:replaced-by-chatgpt|undone-by-image-caption-gender-fixer)(?: \(\d+\))?\.bak$",name)) or bool(re.search(r"-gendeerfixed(?: \(\d+\))?$",path.stem.casefold()))


def parser():
    p = Parser(prog="image_caption_gender_fixer.py", add_help=False,
               description="Local reviewed image text correction. Originals are preserved; history lives in hidden .history.icgf.",
               epilog="Commands: doctor; rules show/add/disable/enable/explain; history status/verify/backup; environment status/repair/cleanup; sessions list/status/abandon; preferences show/set/reset; undo; recover; explain.")
    for flag in ("help", "version", "dry-run", "recursive", "include-hidden", "include-system", "yes", "json", "no-preview", "eco", "verbose", "new-session", "review-no-match-images", "allow-network", "recover-from-backups", "global-rules", "regex"):
        p.add_argument("--"+flag, action="store_true")
    p.add_argument("--skip-reivew-for-confident-ones", "--skip-review-for-confident-ones", dest="skip_confident",action="store_true")
    disposition = p.add_mutually_exclusive_group()
    for flag in ("ask-about-undo-archives", "keep-undo-archives", "recycle-undo-archives"):
        disposition.add_argument("--"+flag,action="store_true")
    p.add_argument("--resume",nargs="?",const="auto")
    p.add_argument("--profile")
    p.add_argument("--priority",type=int,default=10)
    p.add_argument("--scope",choices=["folder","global"],default="folder")
    p.add_argument("--case",choices=["transfer","exact","ignore"],default="transfer")
    p.add_argument("--punctuation",choices=["exact","whitespace","flex"],default="whitespace")
    p.add_argument("--literal-path",action="append",default=[])
    p.add_argument("--context")
    p.add_argument("--image-hash")
    p.add_argument("--session-id")
    p.add_argument("--occurrence")
    p.add_argument("--all-future",action="store_true")
    p.add_argument("--note",default="")
    p.add_argument("items",nargs="*")
    return p


class App:
    def __init__(self, root, args, ask=None):
        self.root,self.args = Path(root),args
        self.args.profile_explicit=self.args.profile is not None
        self.args.profile=self.args.profile or "default"
        self.interactive = not args.json and sys.stdin.isatty()
        self.ask_callback = ask
        if ask is not None and not args.json:
            self.interactive = True
        self.sessions = Sessions(root)
        self.transactions = Transactions(root)
        self.results = []
        self.preference_path = self.root/"runtime/state/preferences.json"
        self.run_disposition = None
        self.context={}
        self.audit=None
        self.cache=HashCache(root)
        if self.cache.warning: self.diagnostics(self.cache.warning)

    def observe_history(self,folder):
        try:
            self.cache.observe(History(folder))
        except (OSError,ValueError,ICGFError) as error:
            self.diagnostics("Derived cache update skipped; folder history remains authoritative: "+str(error))

    def question(self, message, default=""):
        if not self.interactive:
            raise SelectionRequired(message)
        try:
            answer = self.ask_callback(message) if self.ask_callback else input(message)
        except EOFError as error:
            raise Cancelled("Input closed; current image and resumable job retained.",**self.context) from error
        return str(answer).strip() or default

    def region_number(self,regions):
        while True:
            try:
                number=int(self.question("Region number: ","1"))-1
                if not 0<=number<len(regions): raise ValueError
                return number
            except ValueError:
                self.diagnostics("Choose an existing region number between 1 and "+str(len(regions))+".")

    def confirm(self, message):
        return self.question(message,"n").casefold() in ("y","yes")

    def diagnostics(self, message):
        print(message,file=sys.stderr)

    def preferences(self):
        return state_read(self.preference_path,{"undo-corrected":"ask","global-rules":False})

    def rules(self, folder, image_hash=None, session=None):
        store = RuleStore(Path(folder)/".image-gender-fixer.stt")
        local = store.load(self.args.profile,image_hash,session)
        combined = builtins()+local
        toggles={}
        global_store = RuleStore(self.root/"runtime/state/global-rules.stt","global")
        global_rules=global_store.load(self.args.profile,image_hash,session)
        store.ignores += global_store.ignores
        store.warnings += global_store.warnings
        if self.args.global_rules or self.preferences().get("global-rules"):
            combined += global_rules
            toggles.update(global_store.toggles)
        toggles.update(store.toggles)
        for rule in combined:
            if rule.id in toggles: rule.enabled=toggles[rule.id]
        for warning in store.warnings:
            self.diagnostics(warning)
        return combined,store

    def preview(self, path, title):
        if self.args.no_preview or self.args.json or not sys.stdout.isatty():
            return
        chafa = dependencies.native(self.root,"chafa")
        if not chafa:
            raise DependencyUnavailable("Chafa preview unavailable; install it or explicitly choose --no-preview.")
        cols,rows = shutil.get_terminal_size(fallback=(120,40))
        width,height = preview_size(cols,rows)
        print("\n"+title)
        result = subprocess.run([chafa["path"],"--format","symbols","--colors","full","--work","9",
                                 "--animate","off","--scale","max","--size",f"{width}x{height}",str(path)],check=False)
        if result.returncode:
            raise DependencyUnavailable("Chafa preview failed; no approval was inferred.")

    def review(self, source, proposal, regions):
        if not self.interactive:
            raise SelectionRequired(f"Image proposal needs per-image review (level {proposal['level']}). Resume interactively.",**self.context)
        self.preview(source,"Original image")
        for item in proposal["artifacts"]:
            if item["kind"] != "proposal":
                self.preview(item["path"],f"Region {item.get('region',0)+1}: {item['kind']}")
        if proposal.get("stage"):
            self.preview(proposal["stage"],"Complete proposed corrected image")
        if proposal.get("blocked"):
            self.diagnostics("Rendering blocked for region "+str(proposal["blocked"]["region"]+1)+": "+proposal["blocked"]["reason"])
        self.diagnostics("Visual confidence level "+str(proposal["level"])+"; review is required by default.")
        for index,r in enumerate(regions):
            if not r.skipped:
                self.diagnostics(f"{index+1}. {r.before!r} -> {r.after!r}")
        for check in proposal["verification"]:
            if not check["replacement_confirmed"]:
                self.diagnostics("Warning: targeted OCR did not confirm region "+str(check["region"]+1))
        for diagnostic in proposal["diagnostics"]:
            self.diagnostics("Region "+str(diagnostic["index"]+1)+": approximate font "+Path(diagnostic["style"]["font"]).name+
                             "; fit "+str(round(diagnostic["fit_scale"]*100))+"%; repair "+diagnostic["repair"])
            for warning in diagnostic.get("warnings",[]): self.diagnostics("Warning: "+warning)
            self.diagnostics("Font candidates: "+", ".join(Path(c["font"]).name+" ("+str(round(c["score"]*100))+"%)" for c in diagnostic["style"].get("font_candidates",[])))
        if proposal.get("blocked"):
            return self.question("[s]kip, [d]efer, fix [o]CR, [v]isual adjustment, [b]ackground repairs, [i]gnore, [c]ancel: ","c").lower()
        return self.question("[a]pprove, approve+[p]ause, [s]kip, skip+[q]pause, [d]efer, fix [o]CR, [v]isual adjustment, [b]ackground repairs, [i]gnore, [c]ancel: ","c").lower()

    def compare_repairs(self,source,image,region,protected,proposal,remember,index):
        from . import imaging
        from dataclasses import replace
        available=[]
        for method in ("fill","gradient","telea","navier","patch"):
            candidate=replace(region,settings=dict(region.settings,repair=method))
            try:
                _,diagnostic,crops=imaging.render_region(image,candidate,protected)
            except ICGFError as error:
                self.diagnostics(method+": unavailable — "+str(error));continue
            available.append(method)
            for kind in ("repair","corrected"):
                path=Path(source).parent/(".icgf-"+proposal["transaction"]+"-compare-"+str(index+1)+"-"+method+"-"+kind+".png")
                imaging.review_crop(path,crops[kind],"comparison-"+kind,proposal["artifacts"],remember,index)
                self.preview(path,method+": "+kind+"; confidence "+str(diagnostic["level"]))
        while True:
            selected=self.question("Choose repair "+"|".join(available)+", or Enter to retain current: ")
            if not selected: return
            if selected in available:
                region.settings["repair"]=selected;return
            self.diagnostics("Choose one of the displayed repair methods.")

    def cleanup(self, artifacts):
        retained=[]
        for item in artifacts:
            path=Path(item["path"])
            if not path.exists():
                continue
            if not path.name.startswith(".icgf-") or not item.get("identity") or identity(path)[:2]!=item["identity"] or sha256(path)!=item["hash"]:
                retained.append(str(path))
                continue
            try:
                recycle(path)
            except (ICGFError,OSError) as error:
                retained.append(str(path))
                self.diagnostics("Preview retained: "+str(error))
        return retained

    def discover(self, targets, undo=False):
        selected=[]
        explicit=set()
        for target in targets or [str(Path.cwd())]:
            literal=Path(target)
            matches=[str(literal)] if literal.exists() else glob.glob(target)
            if literal.exists(): explicit.add(literal.absolute())
            selected.extend(matches)
        selected.extend(self.args.literal_path)
        explicit.update(Path(p).absolute() for p in self.args.literal_path)
        found,seen=[],set()
        def add(path):
            path=validate_path(path,self.root)
            if is_network(path) and not self.args.allow_network:
                raise UnsafeFilesystem("Network image target refused; use --allow-network explicitly.")
            if path.is_dir():
                for entry in os.scandir(path):
                    child=Path(entry.path)
                    if entry.is_symlink() or reparse(child):
                        continue
                    if child.is_relative_to(self.root):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if self.args.recursive:
                            add(child)
                    elif entry.is_file(follow_symlinks=False):
                        add(child)
                return
            if not path.is_file():
                return
            attributes=getattr(path.stat(),"st_file_attributes",0)
            if not undo and ((attributes&2 and not self.args.include_hidden) or (attributes&4 and not self.args.include_system)):
                return
            key=(path.stat().st_dev,path.stat().st_ino) if path.stat().st_ino else str(path).casefold()
            if key in seen:
                return
            seen.add(key)
            if undo:
                found.append(path)
                return
            name=path.name.casefold()
            if product_name(path):
                return
            with path.open("rb") as handle:
                signature=handle.read(16)
            if signature.startswith(b"\x89PNG\r\n\x1a\n") or signature.startswith(b"\xff\xd8") or signature.startswith((b"GIF87a",b"GIF89a",b"II*\x00",b"MM\x00*")) or (signature.startswith(b"RIFF") and signature[8:12]==b"WEBP"):
                found.append(path)
        for path in selected:
            path=Path(path).absolute()
            if path.is_relative_to(self.root) and path not in explicit: continue
            add(path)
        return sorted(found,key=lambda p:str(p).casefold())

    def select_session(self, paths):
        pending=self.sessions.unfinished()
        if self.sessions.issues:
            self.diagnostics("Session journals need inspection: "+json.dumps(self.sessions.issues))
            if not self.args.new_session and self.args.resume in (None,"auto"):
                raise IntegrityError("Malformed session journals retained; inspect doctor or explicitly select a valid session/new job.")
        if self.args.resume:
            if self.args.resume != "auto":
                return self.sessions.load(self.args.resume)
            if len(pending)==1:
                return pending[0]
            if not pending:
                raise IntegrityError("No resumable session exists.")
        if pending and not self.args.new_session:
            summaries=[self.sessions.summary(s) for s in pending]
            self.diagnostics(json.dumps(summaries,ensure_ascii=False,indent=2))
            if not self.interactive:
                raise SelectionRequired("Resumable sessions exist; select --resume <id> or --new-session.",sessions=summaries)
            choice=self.question("Old jobs: [r]esume, [i]nspect, [t]rash-and-forget, [n]ew while retaining old, [c]ancel: ","c")
            if choice=="n":
                self.diagnostics("Existing jobs retained.")
            elif choice in ("r","i","t"):
                picked=self.question("Session ID: ",pending[0]["id"] if len(pending)==1 else "")
                session=self.sessions.load(picked)
                if choice=="i":
                    self.diagnostics(json.dumps(session,indent=2,ensure_ascii=False))
                    return self.select_session(paths)
                if choice=="t":
                    self.diagnostics("Forgetting this job does not undo committed image changes.")
                    if self.confirm("Recycle this uncommitted queue and its owned artifacts? [y/N] "):
                        self.sessions.abandon(session,self.transactions.pending())
                    return self.select_session(paths)
                return session
            else:
                raise SelectionRequired("New processing canceled; old jobs retained.")
        elif pending:
            self.diagnostics("Starting new job; resumable old jobs remain: "+", ".join(s["id"] for s in pending))
        return self.sessions.create(paths,self.args.profile) if paths else None

    def process(self, targets):
        from . import imaging
        paths=[] if self.args.resume else self.discover(targets)
        if self.args.dry_run:
            result=[]
            for source in paths:
                digest=sha256(source)
                known,_=History(source.parent).recognize(digest)
                if known in ("known_original","known_corrected"):
                    result.append({"file":str(source),"state":"skipped","reason":known})
                    continue
                executable=dependencies.require_ocr(self.root,self.interactive,True,self.confirm)
                image,metadata=imaging.decode(source)
                rules,store=self.rules(source.parent,digest)
                lines=imaging.ocr(image,executable["path"],self.root/"environment/tessdata",self.args.eco)
                regions,_=imaging.regions(lines,rules,store.ignores)
                result.append({"file":str(source),"state":"dry_run","proposed_regions":len(regions),"review_required":bool(regions)})
            return {"state":"dry_run","results":result,"resumable_sessions":[self.sessions.summary(s) for s in self.sessions.unfinished()]},0 if paths else 11
        self.transactions.recover()
        session=self.select_session(paths)
        if not session:
            return {"state":"nothing_to_process","results":[]},11
        if not self.args.profile_explicit:
            self.args.profile=session["profile"]
        self.context={"session":session["id"]}
        if repair_packages(self):
            # Re-enter in a new isolated process so no already-imported broken
            # modules survive the atomic package-tree switch.
            command=[sys.executable,"-B","-I","-S",str(self.root/"image_caption_gender_fixer.py"),"--resume",session["id"],"--profile",self.args.profile]
            for name in ("json","no_preview","eco","verbose","yes","skip_confident","allow_network","review_no_match_images"):
                if getattr(self.args,name,False): command.append("--skip-review-for-confident-ones" if name=="skip_confident" else "--"+name.replace("_","-"))
            if self.interactive and self.ask_callback is None:
                if self.audit: self.audit.record("environment_restart",**self.context)
                os.execv(sys.executable,command)
            restarted=subprocess.run(command,capture_output=True,text=True)
            if restarted.stderr: print(restarted.stderr,file=sys.stderr,end="")
            return json.loads(restarted.stdout),restarted.returncode
        executable=None
        from clairecjs_utils.claire_progressbar import progress_bar
        items=[i for i in session["items"] if i["state"] in ("pending","deferred","failed","interrupted","canceled")]
        deferred_once=set()
        with progress_bar(total=len(items),description="Reviewing images",unit="image",enabled=self.interactive and sys.stderr.isatty() and not self.args.json) as progress:
            for item in items:
                source=Path(item["path"])
                self.context={"session":session["id"]}
                try:
                    if item.get("artifacts"):
                        retained=self.cleanup(item["artifacts"])
                        if retained:
                            self.diagnostics("Earlier previews retained: "+", ".join(retained))
                            item.setdefault("retained_artifacts",[]).extend(a for a in item["artifacts"] if a["path"] in retained)
                        item["artifacts"]=[]
                    if not source.exists():
                        # Reconcile a durable conversion whose session update lagged.
                        if item.get("transaction") and any(r.get("transaction")==item["transaction"] for r in History(source.parent).records):
                            item["state"]="committed"
                            self.sessions.save(session)
                            continue
                        raise IntegrityError("Queued source is unavailable; inspect the job's target.")
                    validate_path(source,self.root)
                    digest=sha256(source)
                    analysis_identity=identity(source)
                    if digest!=item["hash"]:
                        raise IntegrityError("Queued source changed; start a fresh explicitly reviewed job.")
                    folder_history=History(source.parent)
                    known,record=folder_history.recognize(digest)
                    self.observe_history(source.parent)
                    if known is None: known=self.cache.recognize(digest)
                    if known in ("known_original","known_corrected","known_corrected_cross_folder","known_original_cross_folder"):
                        item["state"]="skipped"
                        self.results.append({"file":str(source),"state":"skipped","reason":known})
                        self.sessions.save(session)
                        continue
                    marked=imaging.marker(source)
                    if marked:
                        raise IntegrityError("Image contains an ICGF marker but folder history disagrees; inspect before processing.")
                    image,metadata=imaging.decode(source)
                    if executable is None:
                        executable=dependencies.require_ocr(self.root,self.interactive,False,self.confirm)
                    rules,store=self.rules(source.parent,digest,session["id"])
                    if any(i.get("enabled",True) and i.get("image_hash")==digest and not any(i.get(k) for k in ("phrase","context","occurrence")) for i in store.ignores):
                        item["state"]="skipped"
                        self.sessions.save(session)
                        continue
                    lines=imaging.ocr(image,executable["path"],self.root/"environment/tessdata",self.args.eco)
                    if max(image.size)>1800 and any(w.confidence<80 for line in lines for w in line["words"]):
                        lines=imaging.ocr(image,executable["path"],self.root/"environment/tessdata",self.args.eco,True)
                    regions,protected=imaging.regions(lines,rules,store.ignores)
                    if not regions:
                        if self.args.review_no_match_images:
                            self.preview(source,"No automatic substitution candidate")
                            requested=self.question("Optional manual source phrase -> replacement, or Enter to skip: ")
                            if "->" in requested:
                                before,after=(x.strip() for x in requested.split("->",1))
                                choice=self.question("[o]nce, save [f]older rule, save [g]lobal rule, [i]gnore phrase, [c]ancel: ","o")
                                priority=int(self.question("Numeric priority [10]: ","10"))
                                if choice=="i":
                                    with folder_lock(source.parent):
                                        store.append("ignore",ignore={"phrase":before})
                                elif choice in ("o","f","g"):
                                    new=Rule(before,after,priority,str(uuid.uuid4()),scope="folder",user=True,order=10000)
                                    self.diagnostics("Rule trace: "+json.dumps(transform(before,rules+[new]),ensure_ascii=False))
                                    if choice in ("f","g"):
                                        destination=store if choice=="f" else RuleStore(self.root/"runtime/state/global-rules.stt","global")
                                        with folder_lock(source.parent):
                                            destination.add(before,after,priority,self.args.profile)
                                    rules.append(new)
                                    regions,protected=imaging.regions(lines,rules,store.ignores)
                        if not regions:
                            item["state"]="skipped"
                            self.results.append({"file":str(source),"state":"skipped","reason":"no_substitution"})
                            self.sessions.save(session)
                            continue
                    action=""
                    while True:
                        transaction=str(uuid.uuid4())
                        item.update(transaction=transaction,state="interrupted")
                        self.context={"session":session["id"],"transaction":transaction}
                        self.sessions.save(session)
                        def remember(artifacts):
                            item["artifacts"]=list(artifacts)
                            self.sessions.save(session)
                        proposed=imaging.proposal(source,image,metadata,regions,protected,self.root,executable["path"],digest,
                                                   fingerprint(rules,store.ignores),self.args.eco,transaction,artifact_callback=remember)
                        if not proposed:
                            action="s"
                            break
                        item["artifacts"]=proposed["artifacts"]
                        self.sessions.save(session)
                        if source.stat().st_nlink>1 or known=="previously_undone" or self.args.profile=="conservative":
                            proposed["level"]=max(2,proposed["level"])
                            self.diagnostics("Hard link or previously undone image: explicit review required.")
                        if proposed["level"]==1 and self.args.skip_confident:
                            action="a"
                        else:
                            action=self.review(source,proposed,regions)
                        while proposed.get("blocked") and action in ("a","approve","p","approve and pause"):
                            self.diagnostics("A blocked proposal cannot be approved; correct it, skip, or cancel.")
                            action=self.review(source,proposed,regions)
                        if action in ("a","approve","p","approve and pause"):
                            approved_stage=next(a for a in proposed["artifacts"] if a["kind"]=="proposal")
                            event=self.transactions.commit(source,proposed["stage"],digest,transaction,fingerprint(rules,store.ignores),self.args.profile,proposed["trace"],
                                                           expected_identity=analysis_identity,expected_stage_hash=approved_stage["hash"])
                            item.update(state="committed")
                            self.observe_history(source.parent)
                            self.sessions.save(session)
                            retained=self.cleanup(proposed["artifacts"])
                            item["artifacts"]=[a for a in proposed["artifacts"] if a["path"] in retained]
                            self.sessions.save(session)
                            self.results.append({"file":str(source),"state":"committed","transaction":transaction,
                                                 "corrected":str(source.parent/event["corrected"]),"retained_artifacts":retained})
                            break
                        if action in ("o","ocr"):
                            number=self.region_number(regions)
                            region=regions[number]
                            region.before=self.question("Correct recognized source text: ",region.before)
                            corrected_ocr=transform(region.before,rules,store.ignores)
                            region.after=corrected_ocr["final"]
                            region.trace=corrected_ocr["trace"]
                            region.skipped=not bool(corrected_ocr["edits"])
                            coords=self.question("Correct x1,y1,x2,y2, or Enter to retain box: ")
                            while coords:
                                try:
                                    box=tuple(int(n.strip()) for n in coords.split(","))
                                    if len(box)!=4 or not (0<=box[0]<box[2]<=image.width and 0<=box[1]<box[3]<=image.height): raise ValueError
                                except ValueError:
                                    self.diagnostics("Invalid OCR box; keep it within the image.")
                                    coords=self.question("Correct x1,y1,x2,y2, or Enter to retain box: ");continue
                                old_boxes=[w.box for w in region.words]
                                protected=[p for p in protected if p not in old_boxes]
                                region.box=box
                                region.words=[imaging.Word(region.before,box,region.confidence,0,len(region.before))]
                                protected.append(box)
                                break
                            while True:
                                try:
                                    angle=float(self.question("Rotation in degrees [0]: ","0"))
                                    if not math.isfinite(angle) or not -180<=angle<=180: raise ValueError
                                    region.settings["rotation"]=angle;break
                                except ValueError: self.diagnostics("Use a finite rotation between -180 and 180 degrees.")
                            self.diagnostics("Updated local OCR rule trace: "+json.dumps(transform(region.before,rules),ensure_ascii=False))
                        elif action in ("b","background"):
                            number=self.region_number(regions)
                            self.compare_repairs(source,image,regions[number],protected,proposed,remember,number)
                        elif action in ("v","visual"):
                            number=self.region_number(regions)
                            region=regions[number]
                            while True:
                                command=self.question("Adjustment: smaller/larger; move dx,dy; tracking n; font PATH; color #RRGGBB; outline n; shadow dx,dy,blur; mask +/-n; box x1,y1,x2,y2; rotation n; repair fill|gradient|telea|navier|patch; wording TEXT; skip; reset: ")
                                try:
                                    adjust(region,command,image.size);break
                                except (ArgumentsError,ValueError,OSError) as error:
                                    self.diagnostics("Adjustment was not applied: "+str(error))
                        elif action=="i":
                            number=self.region_number(regions)
                            choice=self.question("Ignore [o]nce, [p]hrase in folder, whole [i]mage, this [s]ession, or [g]lobal phrase: ","o")
                            ignored={"phrase":regions[number].before}
                            if choice=="i":
                                ignored={"image_hash":digest}
                            elif choice=="s":
                                ignored["session"]=session["id"]
                            if choice!="o":
                                destination=RuleStore(self.root/"runtime/state/global-rules.stt","global") if choice=="g" else store
                                with folder_lock(source.parent):
                                    destination.append("ignore",ignore=ignored)
                            regions[number].skipped=True
                        else:
                            break
                        retained=self.cleanup(proposed["artifacts"])
                        if retained:
                            self.diagnostics("Prior proposal artifacts retained: "+", ".join(retained))
                            item.setdefault("retained_artifacts",[]).extend(a for a in proposed["artifacts"] if a["path"] in retained)
                        item["artifacts"]=[]
                    if item["state"]!="committed":
                        if action=="d":
                            item["state"]="deferred"
                            if str(source) not in deferred_once:
                                deferred_once.add(str(source))
                                items.append(item)
                                if progress is not None: progress.total=len(items)
                        elif action in ("s","q"):
                            item["state"]="skipped"
                        else:
                            item["state"]="canceled"
                        self.results.append({"file":str(source),"state":item["state"]})
                        retained=self.cleanup(item.get("artifacts",[]))
                        item["artifacts"]=[a for a in item.get("artifacts",[]) if a["path"] in retained]
                        self.sessions.save(session)
                    if action in ("p","q","c"):
                        break
                except ImageDeferred as error:
                    item.update(state="deferred",error=str(error))
                    self.sessions.save(session)
                    self.results.append({"file":str(source),"state":"deferred","reason":str(error)})
                except (SelectionRequired,Cancelled):
                    self.sessions.save(session)
                    raise
                except (ICGFError,OSError,ValueError,subprocess.SubprocessError) as error:
                    item.update(state="failed",error=str(error))
                    self.sessions.save(session)
                    self.results.append({"file":str(source),"state":"failed","error":str(error),"code":getattr(error,"code",50)})
                except KeyboardInterrupt:
                    self.sessions.save(session)
                    raise
                finally:
                    if progress is not None:
                        progress.update(1)
        failures=any(r["state"]=="failed" for r in self.results)
        summary=self.sessions.summary(session)
        code=50 if failures else 20 if any(r["state"]=="canceled" for r in self.results) else 10 if summary["remaining"] or any(r["state"]!="committed" for r in self.results) else 0
        return {"session":session["id"],"results":self.results,"summary":summary},code


def preview_size(columns,rows):
    return max(1,min(columns-2,max(1,int(columns*.95)))),max(1,min(rows-7,max(1,int(rows*.70))))


def adjust(region, command, size):
    command=command.strip()
    key,_,value=command.partition(" ")
    cfg=region.settings
    if key=="smaller": cfg["scale"]=cfg.get("scale",1)*0.95
    elif key=="larger": cfg["scale"]=cfg.get("scale",1)*1.05
    elif key=="move": cfg["dx"],cfg["dy"]=(int(x) for x in value.split(","))
    elif key=="tracking":
        number=float(value)
        if not math.isfinite(number) or not -8<=number<=64: raise ArgumentsError("Tracking must be between -8 and 64 pixels.")
        cfg["tracking"]=number
    elif key=="font":
        path=Path(value).resolve(strict=True)
        if path.suffix.lower() not in (".ttf",".otf",".ttc"): raise ArgumentsError("Choose a local TrueType/OpenType font file.")
        from . import imaging
        imaging.libraries()[4].truetype(str(path),12)
        cfg["font"]=str(path)
    elif key in ("color","outline-color","shadow-color","label"):
        color=tuple(bytes.fromhex(value.lstrip("#")))
        if len(color)==3: color=color+(255,)
        if len(color)!=4: raise ArgumentsError("Use #RRGGBB or #RRGGBBAA.")
        cfg[{"color":"foreground","outline-color":"outline_color","shadow-color":"shadow_color","label":"label"}[key]]=color
    elif key=="opacity":
        opacity=float(value)
        if not 0<=opacity<=1: raise ArgumentsError("Opacity must be between 0 and 1.")
        cfg["opacity"]=opacity
    elif key=="outline":
        number=int(value)
        if not 0<=number<=64: raise ArgumentsError("Outline must be between 0 and 64 pixels.")
        cfg["outline"]=number
    elif key=="shadow":
        x,y,blur=(float(n) for n in value.split(","))
        if not all(math.isfinite(n) for n in (x,y,blur)) or max(abs(x),abs(y))>max(size) or not 0<=blur<=32: raise ArgumentsError("Invalid shadow offset or blur (0–32 pixels).")
        cfg["shadow"]=(int(x),int(y));cfg["blur"]=blur
    elif key=="mask":
        number=cfg.get("mask",1)+int(value)
        if not -8<=number<=32: raise ArgumentsError("Mask adjustment must stay between -8 and 32 pixels.")
        cfg["mask"]=number
    elif key in ("include","exclude"):
        if value not in ("shadow","outline"): raise ArgumentsError("Choose outline or shadow.")
        cfg["effects"]=(key=="include")
        cfg["mask"]=2 if key=="include" else 0
    elif key=="protect":
        box=tuple(int(n) for n in value.split(","))
        if len(box)!=4 or not(0<=box[0]<box[2]<=size[0] and 0<=box[1]<box[3]<=size[1]): raise ArgumentsError("Invalid protected box.")
        cfg.setdefault("protected",[]).append(box)
    elif key=="extend":
        direction,_,amount=value.partition(" ")
        if direction not in ("left","right","up","down"): raise ArgumentsError("Choose a mask direction.")
        number=int(amount or 1)
        if not 0<=number<=128: raise ArgumentsError("Directional mask extension must be 0–128 pixels.")
        cfg.setdefault("mask_sides",{})[direction]=number
    elif key=="rotation":
        number=float(value)
        if not math.isfinite(number) or not -180<=number<=180: raise ArgumentsError("Rotation must be between -180 and 180 degrees.")
        cfg["rotation"]=number
    elif key=="repair":
        if value not in ("fill","gradient","telea","navier","patch"): raise ArgumentsError("Unknown repair.")
        cfg["repair"]=value
    elif key=="wording":
        if len(value)>4096: raise ArgumentsError("Replacement wording exceeds 4096 characters.")
        region.after=value
    elif key=="box":
        box=tuple(int(n) for n in value.split(","))
        if len(box)!=4 or not(0<=box[0]<box[2]<=size[0] and 0<=box[1]<box[3]<=size[1]): raise ArgumentsError("Invalid box.")
        cfg["box"]=box
    elif key=="skip": region.skipped=True
    elif key=="reset": region.settings={};region.skipped=False
    else: raise ArgumentsError("Unknown visual adjustment.")


def administrative(app, command, values):
    args,root=app.args,app.root
    if command=="doctor":
        from .diagnostics import bundle_health
        unexpected=[str(p) for p in root.iterdir() if (p.is_file() and p.name not in ("image_caption_gender_fixer.py","README.md")) or p.name in ("__pycache__",".pytest_cache")]
        missing=[name for name in ("image_caption_gender_fixer.py","README.md") if not(root/name).is_file()]
        health=bundle_health(root)
        environment=dependencies.status(root,True)
        package_errors={n:v for n,v in environment.get("packages",{}).items() if "error" in v}
        sessions=app.sessions.unfinished()
        retained=[{"session":s["id"],"transaction":i.get("transaction"),"artifacts":i.get("artifacts",[])+i.get("retained_artifacts",[])}
                  for s in sessions for i in s["items"] if i.get("artifacts") or i.get("retained_artifacts")]
        native_errors=[name for name in ("tesseract","chafa") if not environment.get("native",{}).get(name)]
        state_staging=[str(p.relative_to(root)) for p in (root/"runtime/state").rglob(".icgf-state-*.json")]
        return {"root":str(root),"unexpected_items":unexpected,"missing_root_files":missing,
                "pre_existing_at_inspection":unexpected,"introduced_by_doctor":[],"bundle":health,
                "environment":environment,"pending_transactions":app.transactions.pending(),
                "state_staging_retained":state_staging,
                "resumable_sessions":[app.sessions.summary(s) for s in sessions],"session_issues":app.sessions.issues,
                "retained_artifacts":retained},40 if unexpected or missing or health["errors"] or package_errors or native_errors or app.sessions.issues else 0
    if command=="preferences":
        action=values[0] if values else "show"
        preferences=app.preferences()
        if action=="show": return preferences,0
        if args.dry_run: return {"state":"dry_run","requested_preference_action":values},0
        if action=="reset" and values[1:]==["undo-corrected"]:
            preferences["undo-corrected"]="ask"
        elif action=="set" and len(values)==3 and values[1]=="undo-corrected" and values[2] in ("ask","keep","recycle"):
            preferences["undo-corrected"]=values[2]
        elif action=="set" and len(values)==3 and values[1]=="global-rules" and values[2] in ("on","off"):
            preferences["global-rules"]=values[2]=="on"
        elif action=="reset" and values[1:]==["global-rules"]:
            preferences["global-rules"]=False
        else: raise ArgumentsError("Use preferences show/set/reset with undo-corrected ask|keep|recycle or global-rules on|off.")
        state_write(app.preference_path,preferences)
        return {"state":"preference_saved",**preferences},0
    if command in ("history","registry"):
        action=values[0] if values else "status"
        target=Path(values[1]) if len(values)>1 else Path.cwd()
        folder=target if target.is_dir() else target.parent
        validate_path(folder,root)
        history=History(folder)
        if action=="backup":
            if args.dry_run: return {"state":"dry_run","history_backup":str(history.path)},0
            if not history.path.exists(): raise IntegrityError("No folder history exists to back up.")
            with folder_lock(folder):
                dest=available(folder/(".history.icgf.backup."+uuid.uuid4().hex+".jsonl"))
                with history.path.open("rb") as source,dest.open("xb") as out: shutil.copyfileobj(source,out)
                if sha256(dest)!=sha256(history.path): raise IntegrityError("History backup did not verify.")
            return {"state":"history_backed_up","path":str(dest)},0
        if action not in ("status","verify"): raise ArgumentsError("Unknown history command.")
        if action=="verify": history.validate();history.transactions()
        return {"path":str(history.path),"exists":history.path.exists(),"records":len(history.records),
                "integrity_error":history.tail_error,"transactions":len(history.transactions()) if not history.tail_error else None},40 if history.tail_error else 0
    if command=="sessions":
        action=values[0] if values else "list"
        if action=="list": return {"sessions":[app.sessions.summary(s) for s in app.sessions.list()]},0
        if len(values)!=2: raise ArgumentsError("Session ID is required.")
        session=app.sessions.load(values[1])
        if action=="status": return session,0
        if action!="abandon": raise ArgumentsError("Unknown sessions command.")
        if args.dry_run: return {"state":"dry_run","session":session["id"],"operation":"abandon"},0
        app.diagnostics("Forgetting a session preserves committed images, original backups, rules, and .history.icgf; it does not undo completed edits.")
        if not app.confirm("Recycle the uncommitted job and its exact owned artifacts? [y/N] "):
            return {"state":"canceled","session":session["id"]},20
        app.sessions.abandon(session,app.transactions.pending())
        return {"state":"abandoned","session":session["id"]},0
    if command=="environment":
        action=values[0] if values else "status"
        if action=="status": return dependencies.status(root,True),0
        if action=="cleanup":
            from .maintenance import cleanup_downloads
            return {"state":"dry_run" if args.dry_run else "setup_cleanup_complete",
                    "setup_cleanup":cleanup_downloads(root,dry_run=args.dry_run)},0
        if action!="repair": raise ArgumentsError("Unknown environment command.")
        if args.dry_run: return {"state":"dry_run","environment":dependencies.status(root,True)},0
        repaired=repair_packages(app)
        found=dependencies.require_ocr(root,app.interactive,False,app.confirm)
        if repaired:
            checked=subprocess.run([sys.executable,"-B","-I","-S",str(root/"image_caption_gender_fixer.py"),"environment","status","--json"],capture_output=True,text=True,check=True)
            verified=json.loads(checked.stdout)
        else: verified=dependencies.status(root,True)
        return {"state":"environment_verified","ocr":found,"environment":verified},0
    if command=="rules":
        action=values[0] if values else "show"
        rules,local=app.rules(Path.cwd())
        store=RuleStore(root/"runtime/state/global-rules.stt","global") if args.scope=="global" else local
        if action=="show": return {"profile":args.profile,"rules":[asdict(r) for r in rules],"exclusions":local.ignores,"warnings":local.warnings},0
        if action=="profiles": return {"selected":args.profile,"profiles":sorted(set(local.profiles()+RuleStore(root/"runtime/state/global-rules.stt","global").profiles()))},0
        if action=="ignore":
            if len(values)>2: raise ArgumentsError("Use rules ignore [PHRASE] with exclusion selectors.")
            item={}
            if len(values)==2: item["phrase"]=values[1]
            for option,key in (("context","context"),("image_hash","image_hash"),("session_id","session")):
                if getattr(args,option): item[key]=getattr(args,option)
            if args.occurrence:
                try: item["occurrence"]=[int(n) for n in args.occurrence.split(":")]
                except ValueError as error: raise ArgumentsError("Use --occurrence START:END.") from error
            if args.all_future: item["all"]=True
            store.validate_ignore(item)
            if args.dry_run: return {"state":"dry_run","exclusion":item,"profile":args.profile},0
            if args.scope=="folder": validate_path(store.path.parent,root)
            store.path.parent.mkdir(parents=True,exist_ok=True)
            with folder_lock(store.path.parent): saved=store.add_ignore(args.profile,**item)
            return {"state":"exclusion_saved","exclusion":saved,"profile":args.profile},0
        if action=="explain":
            if len(values)<2: raise ArgumentsError("Text is required.")
            return transform(" ".join(values[1:]),rules,local.ignores),0
        if action=="add":
            if len(values)!=3: raise ArgumentsError("Use rules add BEFORE AFTER [--priority N].")
            candidate=Rule(values[1],values[2],args.priority,str(uuid.uuid4()),"regex" if args.regex else "literal",args.case,args.punctuation,args.scope,args.profile,True,len(rules)+100,True)
            preview=transform(values[1],rules+[candidate])
            app.diagnostics("Rule precedence preview: "+json.dumps(preview,ensure_ascii=False))
            if args.dry_run: return {"state":"dry_run","rule":asdict(candidate),"trace":preview},0
            if args.scope=="folder": validate_path(store.path.parent,root)
            store.path.parent.mkdir(parents=True,exist_ok=True)
            with folder_lock(store.path.parent):
                saved=store.add(values[1],values[2],args.priority,args.profile,candidate.mode,args.case,args.punctuation,args.note)
            return {"state":"rule_saved","rule":asdict(saved),"precedence":preview},0
        if action in ("enable","disable"):
            if len(values)!=2: raise ArgumentsError("Rule ID is required.")
            target=next((r for r in rules if r.id==values[1]),None)
            ignored=next((i for i in local.ignores if i.get("id")==values[1]),None)
            if not target and not ignored: raise IntegrityError("No rule or exclusion with that ID exists in this scope.")
            target_id=target.id if target else ignored["id"]
            if args.dry_run: return {"state":"dry_run","action":action,"id":target_id},0
            if args.scope=="folder": validate_path(store.path.parent,root)
            store.path.parent.mkdir(parents=True,exist_ok=True)
            with folder_lock(store.path.parent): store.append(action,id=target_id,profile=args.profile)
            return {"state":action,"id":target_id},0
        raise ArgumentsError("Unknown rules command.")
    if command=="recover":
        if args.dry_run: return {"state":"dry_run","pending":app.transactions.pending()},0
        return {"state":"recovery_checked","transactions":app.transactions.recover()},0
    if command=="explain":
        if len(values)!=1: raise ArgumentsError("explain needs one image path.")
        source=validate_path(Path(values[0]).absolute(),root)
        if not source.is_file(): raise ArgumentsError("Image does not exist.")
        history=History(source.parent)
        digest=sha256(source)
        known,event=history.recognize(digest)
        result={"file":str(source),"sha256":digest,"known_product":known,"transaction":event.get("transaction") if event else None,
                "history_integrity":history.tail_error,"confidence":"unknown","review_required":True}
        if known in ("known_original","known_corrected"):
            result.update(would_process=False,reason=known,review_required=False)
        elif product_name(source):
            result.update(would_process=False,reason="recognized_product_filename",known_product=True,review_required=False)
        elif dependencies.native(root,"tesseract"):
            from . import imaging
            try: image,metadata=imaging.decode(source)
            except ImageDeferred as error:
                result.update(would_process=False,reason="format_deferred",blocking_reason=str(error))
                return result,0
            if imaging.marker(source):
                result.update(would_process=False,reason="marker_history_disagreement",ambiguous=True)
                return result,0
            rules,store=app.rules(source.parent,digest)
            lines=imaging.ocr(image,dependencies.native(root,"tesseract")["path"],root/"environment/tessdata",args.eco)
            regions,protected=imaging.regions(lines,rules,store.ignores)
            result.update(would_process=bool(regions),proposed_regions=len(regions),applicable_rule_ids=sorted({t["rule"] for r in regions for t in r.trace}))
            if regions:
                diagnostics=[];current=image
                try:
                    for region in regions:
                        current,diagnostic,_=imaging.render_region(current,region,protected)
                        diagnostics.append(diagnostic);protected.append(diagnostic["affected"])
                    level=max(d["level"] for d in diagnostics)
                    if known=="previously_undone" or source.stat().st_nlink>1 or args.profile=="conservative": level=max(2,level)
                    result.update(confidence=level,confidence_provisional=True,safe_proposal_available=True)
                except ICGFError as error:
                    result.update(confidence=3,safe_proposal_available=False,blocking_reason=str(error))
            else: result.update(review_required=False,reason="no_substitution")
        else: result.update(would_process=None,reason="OCR unavailable; no installation performed.")
        return result,0
    raise ArgumentsError("Unknown command.")


def repair_packages(app):
    import zipfile
    import hashlib
    state=dependencies.status(app.root,True)
    broken={name:info for name,info in state["packages"].items() if "error" in info}
    if not broken: return
    archive=app.root/"environment/wheels/runtime-bundle.zip"
    manifest_path=app.root/"environment/manifest.json"
    if not archive.exists() or not manifest_path.exists():
        raise DependencyUnavailable("A complete private package repair archive is missing; no global packages were changed.")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    expected=manifest["files"].get("wheels/runtime-bundle.zip",{}).get("sha256")
    if not expected or sha256(archive)!=expected: raise IntegrityError("Package repair archive checksum failed.")
    destination=app.root/"environment"/("packages-"+expected[:16]+"-"+uuid.uuid4().hex[:8])
    unpacked=sum(member.get("size",0) for name,member in manifest["files"].items() if name.startswith("packages/"))
    plan=("Required private Python package repair for "+", ".join(sorted(broken))+". "
          "Source: bundled offline archive "+str(archive)+f" ({archive.stat().st_size:,} bytes; about {unpacked:,} bytes unpacked). "
          "Use the pinned CPython 3.10 x64 package versions from environment/requirements.lock in new directory "+str(destination)+". "
          "Existing package trees are retained. Image correction cannot proceed without the missing dependencies. Install the verified bundle? [y/N] ")
    if not app.confirm(plan):
        raise DependencyUnavailable("Private package repair declined.")
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            relative=Path(member.filename)
            if relative.is_absolute() or ".." in relative.parts or ":" in member.filename or "\\" in member.filename: raise IntegrityError("Unsafe bundled archive entry.")
            if member.is_dir(): continue
            expected_member=manifest["files"].get("packages/"+member.filename,{}).get("sha256")
            if not expected_member or hashlib.sha256(zipped.read(member)).hexdigest()!=expected_member:
                raise IntegrityError("Package repair member failed manifest validation.")
        zipped.extractall(destination)
    verify_code="import sys,os;sys.dont_write_bytecode=True;from pathlib import Path;p=Path(sys.argv[1]);sys.path.insert(0,str(p));handles=[os.add_dll_directory(str(p/n)) for n in ('numpy.libs','PIL','cv2','.dlls') if (p/n).is_dir()];import PIL,numpy,cv2,regex,tqdm,pytest,clairecjs_utils.claire_progressbar;assert all(Path(m.__file__).is_relative_to(p) for m in (PIL,numpy,cv2,regex,tqdm,pytest))"
    subprocess.run([sys.executable,"-B","-I","-S","-c",verify_code,str(destination)],capture_output=True,check=True,timeout=60)
    state_write(destination/".icgf-ready.json",{"bundle_hash":expected,"python":"3.10","architecture":"AMD64"})
    state_write(app.root/"environment/metadata/active.json",{"packages":destination.name})
    from .maintenance import cleanup_downloads, report_cleanup
    report_cleanup(cleanup_downloads(app.root,groups=("python",)),app.diagnostics)
    return True


def undo_images(app, targets):
    if app.args.recover_from_backups:
        return recover_backups(app,targets)
    pairs={}
    for token in targets or [str(Path.cwd())]:
        path=Path(token).absolute()
        folder=path if path.is_dir() else path.parent
        validate_path(folder,app.root)
        if is_network(folder) and not app.args.allow_network: raise UnsafeFilesystem("Network undo requires --allow-network.")
        folders=[folder]
        if path.is_dir() and app.args.recursive:
            queue=[folder]
            while queue:
                current=queue.pop()
                for entry in os.scandir(current):
                    if entry.is_dir(follow_symlinks=False) and not reparse(entry.path):
                        child=validate_path(Path(entry.path),app.root)
                        folders.append(child);queue.append(child)
        for selected in folders:
            history=History(selected)
            history.validate()
            if path.is_dir() or any(c in str(token) for c in "*?["):
                candidates=[r for r in history.transactions().values() if r["event"]!="undone"]
                if not path.is_dir():
                    candidates=[r for r in candidates if any(fnmatch.fnmatchcase(r.get(key,"").casefold(),path.name.casefold()) for key in ("original","corrected","backup"))]
            else:
                candidates=history.resolve(path.name)
            if len(candidates)>1 and not(path.is_dir() or any(c in str(token) for c in "*?")):
                raise IntegrityError("Undo target resolves ambiguously.")
            for record in candidates:
                pairs[(str(selected),record["transaction"])]=(selected,record)
    if not pairs: return {"state":"nothing_to_undo","results":[]},11
    results=[]
    for folder,event in pairs.values():
        if app.args.dry_run:
            results.append({"state":"dry_run","transaction":event["transaction"],"original":event["original"]})
            continue
        record=app.transactions.undo(folder,event)
        app.observe_history(folder)
        archive=Path(record["archive_path"])
        mode="ask"
        if app.args.keep_undo_archives: mode="keep"
        elif app.args.recycle_undo_archives: mode="recycle"
        elif app.args.ask_about_undo_archives: mode="ask"
        else: mode=app.run_disposition or app.preferences().get("undo-corrected","ask")
        if record["changed_corrected"]:
            mode="keep"
            if app.interactive and app.confirm("Corrected image changed since conversion. Explicitly recycle this changed undo archive? [y/N] "):
                mode="recycle"
        elif mode=="ask" and app.interactive:
            choice=app.question("Undo archive: [1]keep [2]recycle [3]keep remaining [4]recycle remaining [5]always keep [6]always recycle [7]cancel/keep: ","1")
            mode="recycle" if choice in ("2","4","6") else "keep"
            if choice in ("3","4"): app.run_disposition=mode
            if choice in ("5","6"):
                preferences=app.preferences();preferences["undo-corrected"]=mode;state_write(app.preference_path,preferences)
        if mode=="recycle":
            try: recycle(archive);record["archive_disposition"]="recycled"
            except (ICGFError,OSError) as error: record.update(archive_disposition="retained",recycle_error=str(error))
        else: record["archive_disposition"]="kept"
        results.append({k:v for k,v in record.items() if k!="trace"})
    return {"state":"undo_complete","results":results},0


def recover_backups(app, targets):
    candidates=[]
    expression=re.compile(r"^(.*)\.bak\.\d{12}\.replaced-by-chatgpt(?: \(\d+\))?\.bak$",re.I)
    for token in targets or [str(Path.cwd())]:
        path=Path(token).absolute()
        expanded=list(path.iterdir()) if path.is_dir() else ([path] if path.exists() else [Path(p) for p in glob.glob(str(path))])
        for candidate in expanded:
            match=expression.match(candidate.name)
            if match: candidates.append((candidate,candidate.with_name(match.group(1))))
    results=[]
    for backup,original in candidates:
        validate_path(backup,app.root)
        if is_network(backup) and not app.args.allow_network: raise UnsafeFilesystem("Network recovery requires --allow-network.")
        if app.args.dry_run:
            results.append({"state":"dry_run","backup":str(backup),"restore":str(original)})
            continue
        if original.exists(): raise UnsafeFilesystem("Recovery original path occupied; no overwrite.")
        if app.confirm(f"History-independent recovery: preserve all corrected images and restore {backup.name} to {original.name}? [y/N] "):
            from .fs import move, source_lease
            expected=sha256(backup)
            with folder_lock(backup.parent),source_lease(backup):
                move(backup,original)
                if sha256(original)!=expected: raise IntegrityError("Recovered original failed verification.")
            results.append({"state":"backup_restored","file":str(original)})
    return {"results":results},0 if results else 11


def main(root, argv=None, ask=None):
    # Windows redirects otherwise inherit an ANSI code page and can fail merely
    # while reporting a valid Unicode path. Keep pipes/files consistently UTF-8.
    for stream in (sys.stdout,sys.stderr):
        if not stream.isatty() and hasattr(stream,"reconfigure"):
            stream.reconfigure(encoding="utf-8",errors="backslashreplace")
    argv=list(sys.argv[1:] if argv is None else argv)
    json_mode="--json" in argv
    audit=None;app=None
    try:
        p=parser()
        args=p.parse_intermixed_args(argv)
        if args.help:
            result={"help":p.format_help()}
            print(json.dumps(result) if args.json else result["help"])
            return 0
        if args.version:
            from .diagnostics import SCHEMAS
            print(json.dumps({"version":__version__,"schema_versions":SCHEMAS}) if args.json else __version__)
            return 0
        if args.resume and args.new_session: raise ArgumentsError("--resume and --new-session conflict.")
        app=App(root,args,ask)
        commands={"doctor","rules","registry","history","preferences","environment","sessions","recover","explain","undo","process"}
        command=args.items[0] if args.items and args.items[0] in commands else "process"
        values=args.items[1:] if args.items and args.items[0] in commands else args.items
        mutating=command in ("process","undo","recover") or command=="environment" and values[:1] in (["repair"],["cleanup"]) or command=="rules" and values[:1] in (["add"],["ignore"],["enable"],["disable"]) or command=="preferences" and values[:1] in (["set"],["reset"]) or command=="sessions" and values[:1]==["abandon"] or command in ("history","registry") and values[:1]==["backup"]
        if mutating and not args.dry_run:
            from .diagnostics import Audit
            audit=Audit(root,command)
            app.audit=audit
        setup_cleanup=None
        if not args.dry_run and (command=="process" or command=="environment" and values[:1]==["repair"]):
            from .maintenance import cleanup_downloads, report_cleanup
            setup_cleanup=cleanup_downloads(root)
            report_cleanup(setup_cleanup,app.diagnostics)
        if command=="process": result,code=app.process(values)
        elif command=="undo": result,code=undo_images(app,values)
        else: result,code=administrative(app,command,values)
        if setup_cleanup and any(setup_cleanup[k] for k in ("recycled","retained")):
            result["setup_cleanup"]=setup_cleanup
        if audit:
            audit.record("finished",code=code,**app.context);audit.close()
        print(json.dumps(result,ensure_ascii=False,default=str,indent=None if args.json else 2))
        return code
    except KeyboardInterrupt:
        result={"state":"canceled","error":"Interrupted; originals and session/recovery state retained."}
        code=20
    except ICGFError as error:
        result={"state":"selection_required" if error.code==21 else "canceled" if error.code==20 else "failed","error":str(error),
                **(app.context if app else {}),**error.context}
        code=error.code
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        result={"state":"failed","error":str(error)}
        code=50
    except Exception as error:
        result={"state":"failed","error":"Unexpected internal error; image/session recovery evidence retained.","exception_type":type(error).__name__}
        code=50
        if audit:
            try: result["crash_report"]=str(audit.crash(error))
            except OSError: result["diagnostic_issue"]="Crash report could not be saved."
    if app: result.update(app.context)
    if app and app.results: result["results"]=app.results
    if audit:
        try: audit.record("stopped",code=code,exception_type=result.get("exception_type"),**(app.context if app else {}));audit.close()
        except OSError: result["diagnostic_issue"]="Operation log could not be finalized."
    print(json.dumps(result,ensure_ascii=False,indent=None if json_mode else 2))
    return code
