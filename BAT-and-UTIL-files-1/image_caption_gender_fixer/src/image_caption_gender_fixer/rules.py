"""Bounded priority cascades with original-character provenance."""
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import uuid
import unicodedata

from .errors import IntegrityError, DependencyUnavailable
from .fs import canonical, now


@dataclass
class Rule:
    before: str
    after: str
    priority: int = 10
    id: str = ""
    mode: str = "literal"
    case: str = "transfer"
    punctuation: str = "whitespace"
    scope: str = "default"
    profile: str = "default"
    enabled: bool = True
    order: int = 0
    user: bool = False
    note: str = ""

    def validate(self):
        if not isinstance(self.before,str) or not isinstance(self.after,str) or not self.before or len(self.before) > 4096 or len(self.after) > 4096:
            raise IntegrityError("Rule text is empty or too long.")
        if self.mode not in ("literal", "regex") or self.case not in ("transfer", "exact", "ignore"):
            raise IntegrityError("Invalid rule mode/case policy.")
        if self.punctuation not in ("exact", "whitespace", "flex"):
            raise IntegrityError("Invalid punctuation policy.")
        if type(self.priority) is not int or not -1000000 <= self.priority <= 1000000:
            raise IntegrityError("Rule priority is invalid.")
        if self.scope not in ("default","folder","global") or not isinstance(self.profile,str) or not self.profile or len(self.profile)>64:
            raise IntegrityError("Rule scope/profile is invalid.")
        if not isinstance(self.enabled,bool) or not isinstance(self.user,bool) or not isinstance(self.order,int) or not isinstance(self.note,str):
            raise IntegrityError("Rule state/order/note is invalid.")


def builtins():
    return [Rule(a, b, p, id="builtin-" + str(i), order=i) for i, (a, b, p) in enumerate([
        ("boi", "boy", 100), ("good boy", "good girl", 10), ("boy", "girl", 10),
        ("man", "woman", 10), ("husband", "wife", 10)])]


def reject_cycles(rules):
    graph = {}
    for rule in rules:
        rule.validate()
        if rule.enabled and rule.mode == "literal":
            graph.setdefault(rule.before.casefold(), set()).add(rule.after.casefold())
    def visit(node, active, done):
        if node in active:
            raise IntegrityError("Direct/indirect literal rule cycle rejected.")
        if node in done:
            return
        for target in graph.get(node, ()):
            visit(target, active | {node}, done)
        done.add(node)
    done = set()
    for node in graph:
        visit(node, set(), done)


def fingerprint(rules,ignores=()):
    return hashlib.sha256(canonical({"rules":[asdict(r) for r in rules],"ignores":list(ignores)}).encode()).hexdigest()


def excluded(item, phrase, start, end, snapshot, origins, original_text):
    """Selectors in one exclusion are conjunctive; separate records are ORed."""
    if not item.get("enabled", True):
        return False
    tests = []
    original = frozenset().union(*(c[1] for c in origins[start:end]))
    a,b=min(original),max(original)+1
    if item.get("phrase") is not None:
        tests.append(any(a < end and start < b for start,end in item["_source_spans"]))
    if item.get("context") is not None:
        tests.append(item["context"].casefold() in original_text.casefold())
    if item.get("occurrence") is not None:
        start,end=item["occurrence"]
        tests.append(a < end and start < b)
    # Image/session/folder/global-only ignores have already been scope-filtered.
    return all(tests) if tests else bool(item.get("image_hash") or item.get("session") or item.get("all"))


def transform(text, rules, ignores=()):
    if not isinstance(text,str) or len(text)>100000:
        raise IntegrityError("Text exceeds the bounded substitution input size.")
    try:
        import regex
    except ImportError as error:
        raise DependencyUnavailable("Bundled regex package is unavailable.") from error
    rules = [r for r in rules if r.enabled]
    prepared=[]
    for item in ignores:
        item=dict(item)
        if item.get("phrase"):
            pattern=r"(?<!\w)"+regex.escape(item["phrase"])+r"(?!\w)"
            item["_source_spans"]=[m.span() for m in regex.finditer(pattern,text,regex.VERSION1|regex.IGNORECASE|regex.FULLCASE,timeout=.15)]
        prepared.append(item)
    reject_cycles(rules)
    priorities = sorted({r.priority for r in rules}, reverse=True)
    if len(priorities) > 64:
        raise IntegrityError("More than 64 priority stages are not supported.")
    # Each output character carries the original character indexes it replaces.
    chars = [(char, frozenset([i]), False) for i, char in enumerate(text)]
    trace, shadowed, stages, states = [], [], [], {text}
    for priority in priorities:
        snapshot = "".join(c[0] for c in chars)
        candidates = []
        for rule in (r for r in rules if r.priority == priority):
            pattern = rule.before
            if rule.mode == "literal":
                parts = rule.before.split()
                joiner = r"\s+" if rule.punctuation == "whitespace" else r"[\s\p{P}]+"
                pattern = regex.escape(rule.before) if rule.punctuation == "exact" else joiner.join(regex.escape(p) for p in parts)
                pattern = r"(?<!\w)(?:" + pattern + r")(?!\w)"
            flags = regex.VERSION1 | (0 if rule.case == "exact" else regex.IGNORECASE | regex.FULLCASE)
            try:
                matches = list(regex.finditer(pattern, snapshot, flags, timeout=0.15))
            except (TimeoutError, regex.error) as error:
                raise IntegrityError("Invalid or excessively expensive regex rule.") from error
            for match in matches:
                a, b = match.span()
                if a == b:
                    raise IntegrityError("Zero-width substitution rules are unsupported.")
                if any(excluded(ignored, match.group(), a, b, snapshot, chars, text) for ignored in prepared):
                    continue
                replacement = rule.after if rule.mode == "literal" else match.expand(rule.after)
                if rule.case == "transfer":
                    if match.group().isupper():
                        replacement = replacement.upper()
                    elif match.group().istitle():
                        replacement = replacement.title()
                candidates.append((a, b, replacement, rule))
        def length(candidate):
            value=unicodedata.normalize("NFC",snapshot[candidate[0]:candidate[1]])
            return len(regex.sub(r"\s+"," ",value).strip())
        candidates.sort(key=lambda c: (-length(c), c[3].mode != "literal", c[3].scope != "folder",
                                       not c[3].user, c[3].order, c[0]))
        selected = []
        for candidate in candidates:
            if any(candidate[0] < chosen[1] and chosen[0] < candidate[1] for chosen in selected):
                shadowed.append({"rule": candidate[3].id, "span": list(candidate[:2]), "priority": priority})
            else:
                selected.append(candidate)
        if not selected:
            continue
        if len(snapshot)+sum(len(c[2])-(c[1]-c[0]) for c in selected)>100000:
            raise IntegrityError("Cascade expansion exceeds the bounded output size.")
        result, offset = [], 0
        for a, b, replacement, rule in sorted(selected, key=lambda c: c[0]):
            result.extend(chars[offset:a])
            origins = frozenset().union(*(c[1] for c in chars[a:b]))
            result.extend((c, origins, True) for c in replacement)
            trace.append({"rule": rule.id, "priority": priority, "before": snapshot[a:b],
                          "after": replacement, "original_span": [min(origins), max(origins)+1]})
            offset = b
        result.extend(chars[offset:])
        chars = result
        intermediate = "".join(c[0] for c in chars)
        stages.append({"priority":priority,"before":snapshot,"after":intermediate,"selected_rules":[c[3].id for c in selected]})
        if intermediate in states:
            raise IntegrityError("Repeated cascade state rejected.")
        states.add(intermediate)
    edits = []
    cursor = 0
    while cursor < len(chars):
        if not chars[cursor][2]:
            cursor += 1
            continue
        end = cursor + 1
        while end < len(chars) and chars[end][2]:
            end += 1
        origins = frozenset().union(*(c[1] for c in chars[cursor:end]))
        edits.append({"start": min(origins), "end": max(origins)+1,
                      "before": text[min(origins):max(origins)+1],
                      "after": "".join(c[0] for c in chars[cursor:end])})
        cursor = end
    for step in trace:
        if step["after"]=="":
            a,b=step["original_span"]
            if not any(e["start"]<=a and b<=e["end"] for e in edits):
                edits.append({"start":a,"end":b,"before":text[a:b],"after":""})
    edits.sort(key=lambda e:e["start"])
    return {"source": text, "final": "".join(c[0] for c in chars), "edits": edits,
            "trace": trace, "shadowed": shadowed,"stages":stages}


class RuleStore:
    def __init__(self, path, scope="folder"):
        self.path, self.scope = Path(path), scope
        self.warnings = []
        self.ignores = []
        self.toggles = {}

    def load(self, profile="default", image_hash=None, session=None):
        self.warnings=[];self.ignores=[];self.toggles={}
        found = {}; ignored = {}
        if not self.path.exists():
            return []
        for index, raw in enumerate(self.path.read_bytes().splitlines()):
            try:
                line=raw.decode("utf-8-sig" if index==0 else "utf-8")
                data = json.loads(line)
                if not isinstance(data,dict): raise ValueError("rule record must be an object")
                if data.get("schema") != 1 or data.get("application") != "icgf":
                    raise ValueError("unsupported rule schema")
                if data["event"] == "rule":
                    fields = data["rule"]
                    rule = Rule(**fields)
                    rule.validate()
                    found[rule.id] = rule
                elif data["event"] in ("enable", "disable"):
                    if data.get("profile","default")!=profile: continue
                    if not isinstance(data.get("id"),str): raise ValueError("toggle ID must be text")
                    self.toggles[data["id"]] = data["event"] == "enable"
                    if data["id"] in found:
                        found[data["id"]].enabled = self.toggles[data["id"]]
                    elif data["id"] in ignored:
                        ignored[data["id"]]["enabled"]=self.toggles[data["id"]]
                    elif not data["id"].startswith(("builtin-","ignore-")):
                        raise ValueError("toggle references an unknown rule")
                elif data["event"] == "ignore":
                    if data.get("profile","default")!=profile: continue
                    item = dict(data["ignore"])
                    self.validate_ignore(item)
                    if item.get("image_hash") not in (None, image_hash) or item.get("session") not in (None, session):
                        continue
                    item.setdefault("id","ignore-"+str(uuid.uuid5(uuid.NAMESPACE_URL,canonical(item))))
                    ignored[item["id"]]=item
                else:
                    raise ValueError("unknown rule event")
            except (KeyError, TypeError, ValueError, IntegrityError) as error:
                self.warnings.append(f"Rule line {index+1} quarantined: {error}")
        self.ignores=list(ignored.values())
        return [r for r in found.values() if r.profile == profile]

    @staticmethod
    def validate_ignore(item):
        if not isinstance(item,dict) or not any(k in item for k in ("phrase","context","image_hash","session","occurrence","all")):
            raise IntegrityError("Exclusion needs at least one selector.")
        for key in ("phrase","context"):
            if key in item and (not isinstance(item[key],str) or not item[key] or len(item[key])>4096):
                raise IntegrityError("Invalid exclusion text selector.")
        if "image_hash" in item and (not isinstance(item["image_hash"],str) or len(item["image_hash"])!=64 or any(c not in "0123456789abcdef" for c in item["image_hash"])):
            raise IntegrityError("Invalid exclusion image hash.")
        if "session" in item:
            if not isinstance(item["session"],str): raise IntegrityError("Invalid exclusion session ID.")
            uuid.UUID(item["session"])
        if "occurrence" in item:
            span=item["occurrence"]
            if not isinstance(span,list) or len(span)!=2 or not all(isinstance(n,int) for n in span) or not 0<=span[0]<span[1]:
                raise IntegrityError("Occurrence must be a nonempty start:end character span.")
        if "all" in item and item["all"] is not True: raise IntegrityError("Invalid whole-scope exclusion.")

    def add_ignore(self, profile="default", **selectors):
        self.validate_ignore(selectors)
        item=dict(selectors,id="ignore-"+str(uuid.uuid4()),enabled=True)
        self.append("ignore",ignore=item,profile=profile)
        return item

    def profiles(self):
        names={"default","conservative"}
        if self.path.exists():
            for raw in self.path.read_bytes().splitlines():
                try:
                    line=raw.decode("utf-8-sig")
                    data=json.loads(line)
                    if data.get("application")=="icgf" and data.get("schema")==1:
                        name=data.get("rule",{}).get("profile",data.get("profile","default"))
                        if isinstance(name,str) and name: names.add(name)
                except (ValueError,AttributeError,TypeError): pass
        return sorted(names)

    def append(self, event, **values):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and not self.path.read_bytes().strip():
            raise IntegrityError("Empty existing rules sidecar is ambiguous.")
        if self.path.exists():
            owned = False
            for raw in self.path.read_bytes().splitlines():
                try:
                    line=raw.decode("utf-8-sig")
                    record = json.loads(line)
                    owned |= isinstance(record,dict) and record.get("application")=="icgf" and record.get("schema")==1
                except (ValueError,TypeError):
                    pass
            if not owned:
                raise IntegrityError("Existing rules file has no recognized ICGF records; it was left intact.")
        data = dict(values, schema=1, application="icgf", timestamp=now(), event=event)
        needs_separator=self.path.exists() and not self.path.read_bytes().endswith(b"\n")
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            if needs_separator: handle.write("\n")
            handle.write(canonical(data) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def add(self, before, after, priority=10, profile="default", mode="literal", case="transfer", punctuation="whitespace", note=""):
        existing = self.load(profile)
        rule = Rule(before, after, priority, str(uuid.uuid4()), mode, case, punctuation,
                    self.scope, profile, True, len(existing)+100, True,note)
        reject_cycles(builtins()+existing+[rule])
        self.append("rule", rule=asdict(rule))
        return rule
