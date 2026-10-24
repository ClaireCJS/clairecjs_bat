"""Bounded priority cascades with original-character provenance."""
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import uuid

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

    def validate(self):
        if not isinstance(self.before,str) or not isinstance(self.after,str) or not self.before or len(self.before) > 4096 or len(self.after) > 4096:
            raise IntegrityError("Rule text is empty or too long.")
        if self.mode not in ("literal", "regex") or self.case not in ("transfer", "exact", "ignore"):
            raise IntegrityError("Invalid rule mode/case policy.")
        if self.punctuation not in ("exact", "whitespace", "flex"):
            raise IntegrityError("Invalid punctuation policy.")
        if not isinstance(self.priority, int) or not -1000000 <= self.priority <= 1000000:
            raise IntegrityError("Rule priority is invalid.")


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


def transform(text, rules, ignores=()):
    try:
        import regex
    except ImportError as error:
        raise DependencyUnavailable("Bundled regex package is unavailable.") from error
    rules = [r for r in rules if r.enabled]
    reject_cycles(rules)
    priorities = sorted({r.priority for r in rules}, reverse=True)
    if len(priorities) > 64:
        raise IntegrityError("More than 64 priority stages are not supported.")
    # Each output character carries the original character indexes it replaces.
    chars = [(char, frozenset([i]), False) for i, char in enumerate(text)]
    trace, shadowed, states = [], [], {text}
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
                if any(ignored.get("phrase", "").casefold() == match.group().casefold() or
                       (ignored.get("context") and ignored["context"].casefold() in snapshot.casefold()) or
                       ignored.get("occurrence") == [a, b] for ignored in ignores):
                    continue
                replacement = rule.after if rule.mode == "literal" else match.expand(rule.after)
                if rule.case == "transfer":
                    if match.group().isupper():
                        replacement = replacement.upper()
                    elif match.group().istitle():
                        replacement = replacement.title()
                candidates.append((a, b, replacement, rule))
        candidates.sort(key=lambda c: (-(c[1]-c[0]), c[3].mode != "literal", c[3].scope != "folder",
                                       not c[3].user, c[3].order, c[0]))
        selected = []
        for candidate in candidates:
            if any(candidate[0] < chosen[1] and chosen[0] < candidate[1] for chosen in selected):
                shadowed.append({"rule": candidate[3].id, "span": list(candidate[:2]), "priority": priority})
            else:
                selected.append(candidate)
        if not selected:
            continue
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
            "trace": trace, "shadowed": shadowed}


class RuleStore:
    def __init__(self, path, scope="folder"):
        self.path, self.scope = Path(path), scope
        self.warnings = []
        self.ignores = []
        self.toggles = {}

    def load(self, profile="default", image_hash=None, session=None):
        self.warnings=[];self.ignores=[];self.toggles={}
        found = {}
        if not self.path.exists():
            return []
        for index, line in enumerate(self.path.read_text(encoding="utf-8").splitlines()):
            try:
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
                    self.toggles[data["id"]] = data["event"] == "enable"
                    if data["id"] in found:
                        found[data["id"]].enabled = self.toggles[data["id"]]
                    elif not data["id"].startswith("builtin-"):
                        raise ValueError("toggle references an unknown rule")
                elif data["event"] == "ignore":
                    item = data["ignore"]
                    if item.get("image_hash") not in (None, image_hash) or item.get("session") not in (None, session):
                        continue
                    self.ignores.append(item)
                else:
                    raise ValueError("unknown rule event")
            except (KeyError, TypeError, ValueError, IntegrityError) as error:
                self.warnings.append(f"Rule line {index+1} quarantined: {error}")
        return [r for r in found.values() if r.profile == profile]

    def append(self, event, **values):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and not self.path.read_text(encoding="utf-8").strip():
            raise IntegrityError("Empty existing rules sidecar is ambiguous.")
        data = dict(values, schema=1, application="icgf", timestamp=now(), event=event)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical(data) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def add(self, before, after, priority=10, profile="default", mode="literal", case="transfer", punctuation="whitespace"):
        existing = self.load(profile)
        rule = Rule(before, after, priority, str(uuid.uuid4()), mode, case, punctuation,
                    self.scope, profile, True, len(existing)+100, True)
        reject_cycles(builtins()+existing+[rule])
        self.append("rule", rule=asdict(rule))
        return rule
