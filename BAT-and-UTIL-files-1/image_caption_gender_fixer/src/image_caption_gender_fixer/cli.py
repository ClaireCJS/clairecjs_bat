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
from .presentation import color,GREEN,YELLOW,CYAN,comparison,Initializing,prompt


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
    return name.startswith((".icgf-",".history.icgf",".image-gender-fixer")) or bool(re.search(r"\.bak\.\d{12}\.(?:replaced-by-chatgpt|undone-by-image-caption-gender-fixer)(?: \(\d+\))?\.bak$",name)) or bool(re.search(r"-(?:genderfixed|gendeerfixed)(?: \(\d+\))*$",path.stem.casefold()))


def parser():
    p = Parser(prog="image_caption_gender_fixer.py", add_help=False,
               description="Local reviewed image text correction. Originals are preserved; history lives in hidden .history.icgf.",
               epilog="Commands: doctor; rules show/add/disable/enable/explain; history status/verify/backup; environment status/repair/cleanup; sessions list/status/abandon; preferences show/set/reset; undo; recover; explain.")
    for flag in ("help", "version", "dry-run", "recursive", "include-hidden", "include-system", "yes", "json", "no-preview", "eco", "verbose", "new-session", "review-no-match-images", "allow-network", "recover-from-backups", "global-rules", "regex"):
        p.add_argument("--"+flag, action="store_true")
    p.add_argument('--ocr','--ocr-only','-o',dest='ocr_only',action='store_true',
                   help='Save OCR ahead of time in hidden .ocr files beside images; no image edits or job selection.')
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
        self.caption_lines=[]
        self.preview_captions={}
        self.floating_artwork=None
        self.ocr_caches={};self.ocr_signatures={};self.ocr_warnings=set()
        self._ocr_progress=None;self._ocr_columns=80
        self.initializing=Initializing(self.interactive and sys.stderr.isatty() and not args.json)
        self.review_rules=[];self.legacy_outputs=[]
        if self.cache.warning: self.diagnostics(self.cache.warning)

    def observe_history(self,folder):
        try:
            self.cache.observe(History(folder))
        except (OSError,ValueError,ICGFError) as error:
            self.diagnostics("Derived cache update skipped; folder history remains authoritative: "+str(error))

    def question(self, message, default=""):
        if not self.interactive:
            raise SelectionRequired(message)
        self.initializing.clear()
        message=prompt(message,default)
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
        self.initializing.clear()
        if self._ocr_progress is not None:
            self.ocr_progress_view(self._ocr_progress,self.context.get('file',''))
            self._ocr_progress.write('\n'.join(ocr_output_lines(message,self._ocr_columns)),file=sys.stderr)
        else:
            print(message,file=sys.stderr)

    def preferences(self):
        return state_read(self.preference_path,{"undo-corrected":"ask","global-rules":False})

    def rules(self, folder, image_hash=None, session=None):
        store = RuleStore(Path(folder)/".image-gender-fixer.stt")
        local = store.load(self.args.profile,image_hash,session)
        combined = builtins()+local
        toggles={};priorities={}
        global_store = RuleStore(self.root/"runtime/state/global-rules.stt","global")
        global_rules=global_store.load(self.args.profile,image_hash,session)
        store.ignores += global_store.ignores
        store.warnings += global_store.warnings
        if self.args.global_rules or self.preferences().get("global-rules"):
            combined += global_rules
            toggles.update(global_store.toggles)
            priorities.update(global_store.priorities)
        toggles.update(store.toggles)
        priorities.update(store.priorities)
        for rule in combined:
            if rule.id in toggles: rule.enabled=toggles[rule.id]
            rule.priority=priorities.get(rule.id,rule.priority)
        for warning in store.warnings:
            self.diagnostics(warning)
        return combined,store

    def preview(self, path, title, detail=False):
        if self.args.no_preview or self.args.json or not sys.stdout.isatty():
            return
        from .paf_backend import terminal_image
        from .floating_artwork import FloatingArtwork
        cols,rows=shutil.get_terminal_size(fallback=(120,40))
        self.initializing.update("Preparing "+title.lower()+"…")
        width,height=preview_size(cols,rows)
        if detail:width,height=max(1,width//5),max(1,height//5)
        payload=terminal_image(self.root,path,width,height)
        self.initializing.clear()
        print("\n"+color(title,CYAN),flush=True)
        self.write_terminal_image(payload)
        if self.floating_artwork is None: self.floating_artwork=FloatingArtwork(self.root)
        self.floating_artwork.update(path,title,self.preview_captions)

    @staticmethod
    def write_terminal_image(payload):
        sys.stdout.flush()
        sys.stdout.buffer.write(payload+b"\n");sys.stdout.buffer.flush()

    def close_previews(self):
        if self.floating_artwork is not None:
            self.floating_artwork.close()
            self.floating_artwork=None

    def review(self, source, proposal, regions):
        if not self.interactive:
            raise SelectionRequired(f"Image proposal needs per-image review (level {proposal['level']}). Resume interactively.",**self.context)
        from .imaging import full_captions
        captions=full_captions(self.caption_lines,regions)
        self.preview_captions=captions
        self.preview(source,"Original image")
        for item in proposal["artifacts"]:
            if item["kind"]!="proposal":
                self.preview(item["path"],f"Region {item.get('region',0)+1}: {item['kind']}",detail=True)
        if proposal.get("stage"): self.preview(proposal["stage"],"Complete proposed corrected image")
        self.diagnostics("\n"+comparison(captions["detected"],captions["proposed"])+"\n")
        if proposal.get("blocked"):
            self.diagnostics("Rendering blocked for region "+str(proposal["blocked"]["region"]+1)+": "+proposal["blocked"]["reason"])
        self.diagnostics("Visual confidence level "+str(proposal["level"])+"; review is required by default.")
        for index,r in enumerate(regions):
            if not r.skipped:
                self.diagnostics(f"{index+1}. "+color(repr(r.before),GREEN)+" ➜ "+color(repr(r.after),YELLOW))
        for check in proposal["verification"]:
            if not check["replacement_confirmed"]:
                self.diagnostics(color("⚠️ Targeted OCR did not confirm region "+str(check["region"]+1),YELLOW))
        for diagnostic in proposal["diagnostics"]:
            self.diagnostics("Region "+str(diagnostic["index"]+1)+": approximate font "+Path(diagnostic["style"]["font"]).name+
                             "; fit "+str(round(diagnostic["fit_scale"]*100))+"%; repair "+diagnostic["repair"])
            for warning in diagnostic.get("warnings",[]): self.diagnostics(color("⚠️ "+warning,YELLOW))
            self.diagnostics("Font candidates: "+", ".join(Path(c["font"]).name+" ("+str(round(c["score"]*100))+"%)" for c in diagnostic["style"].get("font_candidates",[])))
        menu=('[y]approve, approve+[p]ause, ' if not proposal.get('blocked') else '')+'[a]dd rule, [e]dit caption, [s]kip, skip+[q]pause, [d]efer, fix [o]CR, [v]isual adjustment, [b]ackground repairs, [i]gnore, [c]ancel: '
        self.review_notes=[warning for diagnostic in proposal['diagnostics'] for warning in diagnostic.get('warnings',[])]
        if proposal.get('blocked'):self.review_notes.insert(0,proposal['blocked']['reason'])
        if any(not check['replacement_confirmed'] for check in proposal['verification']):self.review_notes.append('Targeted OCR did not confirm every replacement; inspect the rendered image.')
        return self.review_question(menu,proposal.get('blocked'))

    def review_question(self,message,blocked):
        artwork=self.floating_artwork
        if artwork is None or self.ask_callback is not None or os.name!='nt':
            answer=self.question(message,'s').lower()
            return {'y':'a','a':'add_rule','e':'edit_caption'}.get(answer,answer)
        import msvcrt,time
        token=artwork.begin_review(blocked,self.review_rules,getattr(self,"review_notes",[]))
        sys.stderr.write(prompt(message,'s'));sys.stderr.flush();typed=''
        try:
            while True:
                action=artwork.review_action(token)
                if action is not None:
                    while msvcrt.kbhit():msvcrt.getwch()
                    sys.stderr.write('\n');sys.stderr.flush();return action
                if artwork.stopped.is_set():raise DependencyUnavailable('Artwork window stopped during review; proposal retained.')
                if msvcrt.kbhit():
                    key=msvcrt.getwch()
                    if key=='\x03':raise KeyboardInterrupt
                    if key in ('\x00','\xe0'):msvcrt.getwch();continue
                    if key=='\r':
                        sys.stderr.write('\n');sys.stderr.flush()
                        answer=typed.strip().lower() or 's'
                        return {'y':'a','a':'add_rule','e':'edit_caption'}.get(answer,answer)
                    if key=='\b':
                        if typed:typed=typed[:-1];sys.stderr.write('\b \b')
                    elif key.isprintable():typed+=key;sys.stderr.write(key)
                    sys.stderr.flush()
                time.sleep(.03)
        finally:artwork.end_review(token)

    def edit_caption(self):
        # Prefilled native editor, also available when terminal previews are off.
        from .caption_editor import edit_caption
        return edit_caption(self.preview_captions.get('proposed',''))

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
                self.preview(path,method+": "+kind+"; confidence "+str(diagnostic["level"]),detail=True)
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
        self.initializing.update("Discovering image files…")
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
            if len(seen)%25==0:self.initializing.update(f"Discovering images: {len(seen):,} files checked, {len(found):,} images found…")
            if undo:
                found.append(path)
                return
            name=path.name.casefold()
            if name=='.ocr': return
            if product_name(path):
                from .name_migration import corrected_name
                if corrected_name(path) and path not in self.legacy_outputs:self.legacy_outputs.append(path)
                return
            with path.open("rb") as handle:
                signature=handle.read(16)
            if signature.startswith(b"\x89PNG\r\n\x1a\n") or signature.startswith(b"\xff\xd8") or signature.startswith((b"GIF87a",b"GIF89a",b"II*\x00",b"MM\x00*")) or (signature.startswith(b"RIFF") and signature[8:12]==b"WEBP"):
                found.append(path)
        for path in selected:
            path=Path(path).absolute()
            if path.is_relative_to(self.root) and path not in explicit: continue
            add(path)
        if not undo and self.legacy_outputs:
            from .name_migration import migrate,corrected_name
            for legacy in self.legacy_outputs:
                if self.args.dry_run:self.diagnostics('Would rename '+legacy.name+' ➜ '+corrected_name(legacy))
                else:
                    pending=[r for r in self.transactions.pending() if Path(r['folder'])==legacy.parent]
                    if pending:
                        self.diagnostics('Filename repair waits for correction recovery: '+legacy.name);continue
                    result=migrate(self.transactions.root,legacy)
                    if result:self.diagnostics('🔤 Renamed '+Path(result['from']).name+' ➜ '+Path(result['to']).name)
            self.legacy_outputs=[]
        return sorted(found,key=lambda p:str(p).casefold())

    def show_jobs(self,pending):
        from datetime import datetime
        self.diagnostics('\nUnfinished image jobs:')
        for number,session in enumerate(pending,1):
            summary=self.sessions.summary(session)
            try: updated=datetime.fromisoformat(session['updated']).astimezone().strftime('%Y-%m-%d %I:%M %p')
            except ValueError: updated=session['updated']
            folders=list(dict.fromkeys(str(Path(item['path']).parent) for item in session['items']))
            self.diagnostics(f"  {number}. {folders[0] if folders else '(empty queue)'}"+
                             (f' (+{len(folders)-1} other folders)' if len(folders)>1 else ''))
            self.diagnostics(f"     Updated {updated}; {len(session['items'])} images; {summary['remaining']} remaining; "+
                             f"{summary['completed']} corrected; {summary['counts'].get('skipped',0)} skipped; profile {session['profile']}")

    def pick_jobs(self,pending,allow_all=False):
        if len(pending)==1: return [pending[0]]
        while True:
            answer=self.question(f"Job number [1-{len(pending)}]"+(' or [a]ll' if allow_all else '')+", [b]ack, [?]help: ").casefold()
            if answer in ('b','back','c','cancel'): return []
            if allow_all and answer in ('a','all'): return pending
            if answer.isdecimal() and 1<=int(answer)<=len(pending): return [pending[int(answer)-1]]
            # Existing scripted callers may still supply the stable ID.
            selected=next((session for session in pending if session['id']==answer),None)
            if selected: return [selected]
            self.diagnostics('Choose the number beside the job'+(' or a for all jobs' if allow_all else '')+'. No session ID is needed. Use b to go back.')

    def select_session(self, paths):
        while True:
            selected=self._select_session_once(paths)
            if selected is not False: return selected

    def _select_session_once(self, paths):
        pending=self.sessions.unfinished()
        pending.sort(key=lambda session:(session['updated'],session['created'],session['id']),reverse=True)
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
            if not self.interactive:
                raise SelectionRequired("Resumable sessions exist; select --resume <id> or --new-session.",sessions=summaries)
            self.show_jobs(pending)
            choice=self.question("Jobs: [r]esume, [i]nspect, [t]rash-and-forget, [n]ew while retaining old, [c]ancel, [?]help: ","c").casefold()
            choice={'resume':'r','inspect':'i','trash':'t','new':'n','cancel':'c'}.get(choice,choice)
            if choice.isdecimal() and 1<=int(choice)<=len(pending): return pending[int(choice)-1]
            if choice=="n":
                self.diagnostics("Existing jobs retained.")
            elif choice in ("r","i","t"):
                picked=self.pick_jobs(pending,allow_all=choice=='t')
                if not picked: return False
                session=picked[0]
                if choice=="i":
                    self.show_jobs(picked)
                    for item in session['items'][:20]: self.diagnostics('     '+item['state']+': '+item['path'])
                    if len(session['items'])>20: self.diagnostics(f"     ... {len(session['items'])-20} more images")
                    return False
                if choice=="t":
                    self.diagnostics('Original images are retained. Forgetting jobs does not undo committed image changes.')
                    if self.confirm(f"Recycle {len(picked)} selected job queue(s) and their owned previews? [y/N] "):
                        for session in picked: self.sessions.abandon(session,self.transactions.pending())
                    return False
                return session
            elif choice=='c':
                raise SelectionRequired("New processing canceled; old jobs retained.")
            else:
                self.diagnostics('Resume continues an unfinished job; inspect shows its queued images; trash recycles selected queues/previews; new uses the current targets and keeps old jobs. Choose a job by number, not its internal ID.')
                return False
        elif pending:
            self.diagnostics("Starting new job; resumable old jobs remain: "+", ".join(s["id"] for s in pending))
        return self.sessions.create(paths,self.args.profile,self.initializing.update) if paths else None

    def restart_repaired(self,options):
        command=[sys.executable,'-B','-I','-S',str(self.root/'image_caption_gender_fixer.py'),*options]
        for name in ('json','no_preview','eco','verbose','yes','skip_confident','allow_network','review_no_match_images'):
            if getattr(self.args,name,False): command.append('--skip-review-for-confident-ones' if name=='skip_confident' else '--'+name.replace('_','-'))
        if self.interactive and self.ask_callback is None:
            if self.audit: self.audit.record('environment_restart',**self.context);self.audit.close()
            raise SystemExit(os.spawnv(os.P_WAIT,sys.executable,command))
        restarted=subprocess.run(command,capture_output=True,text=True)
        if restarted.stderr: print(restarted.stderr,file=sys.stderr,end='')
        return json.loads(restarted.stdout),restarted.returncode

    def ocr_lines(self,source,image,digest,executable,persist=False,expected_identity=None):
        from .ocr_cache import OCRCache,signature,recognize
        folder=Path(source).parent
        cache=self.ocr_caches.setdefault(folder,OCRCache(folder))
        settings=None
        if persist or os.path.lexists(cache.path):
            stamp=(str(executable['path']),self.args.eco)
            if stamp not in self.ocr_signatures: self.ocr_signatures[stamp]=signature(self.root,executable['path'],self.args.eco)
            settings=self.ocr_signatures[stamp]
            try:
                lines=cache.get(digest,settings,image.size)
                if cache.warning and folder not in self.ocr_warnings:
                    self.diagnostics(cache.warning);self.ocr_warnings.add(folder)
                if lines is not None: return lines,True
            except (ICGFError,OSError,ValueError) as error:
                if persist: raise
                if folder not in self.ocr_warnings:
                    self.diagnostics('Saved OCR unavailable; recognizing again: '+str(error));self.ocr_warnings.add(folder)
        lines=recognize(image,executable['path'],self.root/'environment/tessdata',self.args.eco)
        if persist:
            if identity(source)!=expected_identity or sha256(source)!=digest:
                raise IntegrityError('Image changed during OCR; result was not cached. Run OCR again for this image.')
            cache.put(source,digest,settings,image.size,lines)
        return lines,False

    def ocr_console_enabled(self):
        return self.args.ocr_only and self.interactive and not self.args.json and sys.stdout.isatty() and sys.stderr.isatty()

    def ocr_progress_view(self,progress,source,refresh=True):
        """Configure the shared rainbow bar; never draw a separate progress bar."""
        if progress is None: return
        from tqdm.utils import disp_len
        columns=progress.ncols or 80
        if callable(progress.dynamic_ncols):
            columns=progress.dynamic_ncols(progress.fp)[0] or columns
        width=min(140,max(1,int(columns)-1))
        if width<self._ocr_columns:
            # tqdm's old-width padding can wrap after a console is narrowed.
            # Reset its own line printer and erase only the current line.
            progress.fp.write('\r\x1b[K')
            progress.sp=progress.status_printer(progress.fp)
        self._ocr_columns=width
        if width>=110:
            layout='OCR {n_fmt}/{total_fmt} {percentage:3.0f}% |{bar:20}| {elapsed}<{remaining} {rate_fmt}{postfix}'
        elif width>=75:
            layout='OCR {n_fmt}/{total_fmt} {percentage:3.0f}% |{bar:12}| ETA {remaining}{postfix}'
        elif width>=40:
            layout='OCR {n_fmt}/{total_fmt} {percentage:3.0f}% ETA {remaining}{postfix}'
        else:
            layout='{n_fmt}/{total_fmt} {percentage:3.0f}%'
        progress.bar_format=layout
        info=dict(progress.format_dict,bar_format=layout,postfix='',ncols=None)
        fixed=disp_len(progress.format_meter(**info))
        # Leave room for the next counter digit and a newly estimated rate.
        filename=ocr_fit_text(ocr_display_text(Path(source).name),max(0,width-fixed-14),ellipsis=True)
        progress.set_postfix_str(filename,refresh=refresh)

    def print_ocr_summary(self,result):
        if not self.ocr_console_enabled(): return False
        if result.get('state')=='nothing_to_ocr':
            print('No matching images to OCR.');return True
        items=result.get('results',[])
        ready=sum(item['state']=='ocr_cached' for item in items)
        reused=sum(bool(item.get('reused')) for item in items)
        failed=sum(item['state']=='failed' for item in items)
        deferred=sum(item['state']=='deferred' for item in items)
        label='OCR stopped' if result.get('state')=='canceled' else 'OCR finished'
        lines=[f'{label}: {ready:,} ready ({ready-reused:,} newly saved, {reused:,} reused), {deferred:,} deferred, {failed:,} failed.']
        folders={str(Path(item['cache']).parent) for item in items if item.get('cache')}
        if len(folders)==1: lines.append('Saved OCR: '+str(Path(next(iter(folders)))/'.ocr'))
        elif folders: lines.append(f'Saved OCR: hidden .ocr files in {len(folders):,} image folders.')
        if result.get('error'): lines.append(result['error'])
        if ready and not self.args.verbose: lines.append('Full captions: icgf -o --verbose (reuses saved OCR).')
        print('\n'.join(line for message in lines for line in ocr_output_lines(message,self._ocr_columns)))
        return True

    def prefetch_ocr(self,targets):
        from . import imaging
        if self.args.resume or self.args.dry_run:
            raise ArgumentsError('--ocr-only cannot be combined with --resume or --dry-run; supply image targets to prepare OCR.')
        paths=self.discover(targets)
        if not paths: return {'state':'nothing_to_ocr','results':[]},11
        self.initializing.update("Checking private dependency bundle…")
        if repair_packages(self):
            options=['--ocr-only']
            for path in paths: options.extend(['--literal-path',str(path)])
            return self.restart_repaired(options)
        executable=dependencies.require_ocr(self.root,self.interactive,False,self.confirm)
        results=[];self.results=results
        console=self.ocr_console_enabled()
        if console:
            self.diagnostics('\n'.join(ocr_output_lines(
                f'Preparing OCR for {len(paths):,} images. Results stay in hidden .ocr files beside the images.',self._ocr_columns)))
        from clairecjs_utils.claire_progressbar import progress_bar
        with progress_bar(total=len(paths),description='OCR',unit='image',enabled=console,
                          bar_format='OCR {n_fmt}/{total_fmt} {percentage:3.0f}% |{bar:12}| ETA {remaining}') as progress:
            self._ocr_progress=progress
            try:
                for source in paths:
                    self.context={'file':str(source)}
                    self.ocr_progress_view(progress,source)
                    try:
                        original_identity=identity(source);digest=sha256(source)
                        image,_metadata=imaging.decode(source)
                        lines,reused=self.ocr_lines(source,image,digest,executable,True,original_identity)
                        if identity(source)!=original_identity or sha256(source)!=digest:
                            raise IntegrityError('Image changed during OCR; rerun OCR before using its result.')
                        caption=imaging.full_captions(lines,[])['detected']
                        results.append({'file':str(source),'state':'ocr_cached','reused':reused,
                                        'cache':str(source.parent/'.ocr'),'caption':caption,'lines':len(lines)})
                        if console and self.args.verbose:
                            heading=f"[{len(results)}/{len(paths)}] "+('REUSED' if reused else 'SAVED')+'  '+source.name
                            block=list(ocr_output_lines(heading,self._ocr_columns))
                            block.append('  Entire detected caption:')
                            block.extend(ocr_output_lines(caption or '(No text detected)',self._ocr_columns,indent='    '))
                            self.diagnostics('\n'.join(block)+'\n')
                    except ImageDeferred as error:
                        results.append({'file':str(source),'state':'deferred','reason':str(error)})
                        if console: self.diagnostics('DEFERRED '+source.name+': '+str(error))
                    except (ICGFError,OSError,ValueError,subprocess.SubprocessError) as error:
                        results.append({'file':str(source),'state':'failed','error':str(error)})
                        if console: self.diagnostics('FAILED '+source.name+': '+str(error))
                    finally:
                        if progress is not None:
                            self.ocr_progress_view(progress,source,refresh=False)
                            progress.update(1)
            finally:
                self._ocr_progress=None
        counts={state:sum(item['state']==state for item in results) for state in ('ocr_cached','deferred','failed')}
        counts['reused']=sum(item.get('reused',False) for item in results)
        return {'state':'ocr_only','results':results,'summary':counts},50 if counts['failed'] else 10 if counts['deferred'] else 0

    def process(self, targets):
        self.initializing.update("Loading image processing libraries…")
        from . import imaging
        if self.args.ocr_only: return self.prefetch_ocr(targets)
        if not self.args.dry_run:
            self.initializing.update('Checking interrupted transactions and filename repairs…')
            from .name_migration import recover as recover_names
            recover_names(self.transactions.root);self.transactions.recover()
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
                lines,_=self.ocr_lines(source,image,digest,executable)
                regions,_=imaging.regions(lines,rules,store.ignores)
                result.append({"file":str(source),"state":"dry_run","proposed_regions":len(regions),"review_required":bool(regions)})
            return {"state":"dry_run","results":result,"resumable_sessions":[self.sessions.summary(s) for s in self.sessions.unfinished()]},0 if paths else 11
        self.initializing.update("Checking interrupted transactions…")
        self.transactions.recover()
        session=self.select_session(paths)
        if not session:
            return {"state":"nothing_to_process","results":[]},11
        if not self.args.profile_explicit:
            self.args.profile=session["profile"]
        self.context={"session":session["id"]}
        self.initializing.update("Checking private dependency bundle…")
        if repair_packages(self):
            # Re-enter in a new isolated process so no already-imported broken
            # modules survive the atomic package-tree switch.
            return self.restart_repaired(['--resume',session['id'],'--profile',self.args.profile])
        executable=None
        from clairecjs_utils.claire_progressbar import progress_bar
        items=[i for i in session["items"] if i["state"] in ("pending","deferred","failed","interrupted","canceled")]
        deferred_once=set()
        self.initializing.clear()
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
                    self.initializing.update("Decoding "+source.name+"…")
                    image,metadata=imaging.decode(source)
                    if executable is None:
                        executable=dependencies.require_ocr(self.root,self.interactive,False,self.confirm)
                    rules,store=self.rules(source.parent,digest,session["id"])
                    if any(i.get("enabled",True) and i.get("image_hash")==digest and not any(i.get(k) for k in ("phrase","context","occurrence")) for i in store.ignores):
                        item["state"]="skipped"
                        self.sessions.save(session)
                        continue
                    self.initializing.update("Loading saved OCR / recognizing caption…")
                    lines,reused_ocr=self.ocr_lines(source,image,digest,executable)
                    if reused_ocr and self.interactive: self.diagnostics('Using saved OCR: '+source.name)
                    self.caption_lines=lines
                    regions,protected=imaging.regions(lines,rules,store.ignores)
                    self.preview_captions=imaging.full_captions(lines,regions)
                    if not regions:
                        if self.interactive:
                            self.diagnostics("\n"+source.name+" — entire detected caption:\n"+imaging.full_captions(lines,[])["detected"])
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
                    action="";manual_caption=None
                    while True:
                        transaction=str(uuid.uuid4())
                        item.update(transaction=transaction,state="interrupted")
                        self.context={"session":session["id"],"transaction":transaction}
                        self.sessions.save(session)
                        def remember(artifacts):
                            item["artifacts"]=list(artifacts)
                            self.sessions.save(session)
                        self.initializing.update("Rendering and verifying proposed caption…")
                        self.review_rules=rules
                        proposed=imaging.proposal(source,image,metadata,regions,protected,self.root,executable["path"],digest,
                                                   fingerprint(rules,store.ignores),self.args.eco,transaction,artifact_callback=remember)
                        self.initializing.clear()
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
                        while proposed.get("blocked") and isinstance(action,str) and action in ("a","approve","p","approve and pause"):
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
                        payload=action if isinstance(action,dict) else {'action':action}
                        if payload['action']=='add_rule':
                            from .rule_editor import console_editor,validate_payload
                            try:
                                values=payload.get('payload') or console_editor(self,rules)
                                if values is not None:
                                    ordered,new=validate_payload(values,rules,self.args.profile)
                                    with folder_lock(source.parent):store.save_order(ordered,new,self.args.profile)
                                    rules,store=self.rules(source.parent,digest,session['id'])
                                    if manual_caption is None:regions,protected=imaging.regions(self.caption_lines,rules,store.ignores)
                                    else:
                                        from .caption_editor import caption_regions
                                        manual_caption='\n'.join(transform(line,rules,store.ignores)['final'] for line in manual_caption.splitlines())
                                        regions,protected=caption_regions(self.caption_lines,manual_caption)
                                    self.diagnostics('➕ Substitution saved; rebuilding proposal.')
                            except (IntegrityError,ValueError,KeyError) as error:self.diagnostics('Substitution was not saved: '+str(error))
                        elif payload['action']=='edit_caption':
                            from .caption_editor import caption_regions
                            text=payload.get('text') if 'text' in payload else self.edit_caption()
                            if text is not None:
                                try:
                                    regions,protected=caption_regions(self.caption_lines,text);manual_caption=text
                                except IntegrityError as error:self.diagnostics('Caption was not changed: '+str(error))
                        elif action in ("o","ocr"):
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


def ocr_display_text(text):
    """Keep OCR text visible instead of interpreting stray terminal controls."""
    return ''.join(char if char in '\n\t' or not(ord(char)<32 or 127<=ord(char)<=159)
                   else ('\\x'+format(ord(char),'02x')) for char in str(text)).expandtabs(4)


def ocr_fit_text(text,width,ellipsis=False):
    import unicodedata
    if width<=0: return ''
    def fit(value,limit):
        used=0;answer=[]
        for char in value:
            cost=0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in 'FW' else 1
            if used+cost>limit: break
            used+=cost;answer.append(char)
        return ''.join(answer)
    answer=fit(text,width)
    return fit(text,width-3)+'...' if ellipsis and len(answer)<len(text) and width>=3 else answer


def ocr_output_lines(text,width,indent=''):
    width=max(len(indent)+2,int(width)-1)
    for line in ocr_display_text(text).split('\n'):
        if not line: yield '';continue
        while line:
            part=ocr_fit_text(line,width-len(indent))
            if len(part)<len(line) and part.rfind(' ')>len(part)//2: part=part[:part.rfind(' ')]
            yield indent+part
            line=line[len(part):].lstrip(' ')


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
        native_errors=[name for name in ("tesseract",) if not environment.get("native",{}).get(name)]
        from .paf_album_art import availability
        preview=availability(root)
        state_staging=[str(p.relative_to(root)) for p in (root/"runtime/state").rglob(".icgf-state-*.json")]
        return {"root":str(root),"unexpected_items":unexpected,"missing_root_files":missing,
                "pre_existing_at_inspection":unexpected,"introduced_by_doctor":[],"bundle":health,
                "environment":environment,"preview":preview,"pending_transactions":app.transactions.pending(),
                "state_staging_retained":state_staging,
                "resumable_sessions":[app.sessions.summary(s) for s in sessions],"session_issues":app.sessions.issues,
                "retained_artifacts":retained},40 if unexpected or missing or health["errors"] or package_errors or native_errors or not preview["available"] or app.sessions.issues else 0
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
    state=dependencies.status(app.root,True,getattr(getattr(app,"initializing",None),"update",None))
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
        if args.ocr_only and command!='process': raise ArgumentsError('--ocr-only applies to image processing targets, not administrative commands.')
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
        if not app.print_ocr_summary(result):
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
    finally:
        if app: app.initializing.clear();app.close_previews()
    if app: result.update(app.context)
    if app and app.results: result["results"]=app.results
    if audit:
        try: audit.record("stopped",code=code,exception_type=result.get("exception_type"),**(app.context if app else {}));audit.close()
        except OSError: result["diagnostic_issue"]="Operation log could not be finalized."
    if not(app and app.print_ocr_summary(result)):
        print(json.dumps(result,ensure_ascii=False,indent=None if json_mode else 2))
    return code
