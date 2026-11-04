#!/usr/bin/env python3
"""Report over-budget comments and over-long functions, scoped to changed lines.

    find-violations.py <file> [<file>...]        # vs merge-base with the default branch
    find-violations.py --base <ref> <file>...    # vs another ref
    find-violations.py --all <file>...           # ignore git; audit the whole file
    find-violations.py --summary <file>...       # one line per file

Each finding prints its exact cap ("-> MAX N LINES"). Rewrite to that number. Editing shifts
line numbers, so re-run until it reports nothing.
"""
import argparse, os, re, subprocess, sys

EXTS = (".rs", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".swift", ".c", ".h", ".cpp", ".py")
SKIP = re.compile(r"(^|/)(node_modules|target|dist|build|vendor|\.next)/|/idl/|\.generated\.|\.min\.|\.d\.ts$")
COMMENT_TARGET = 4
ALLOW_VERBOSE = re.compile(r"allow-verbose:")          # a comment this short never trips the ratio
MAX_FN_LINES = 80
MAX_DECL_COMMENTS = 3       # comments explaining a name, per function


def line_prefix(path):
    return "#" if path.endswith(".py") else "//"


def changed_lines(path, base):
    """1-based lines differing from `base` in the working tree. None means audit everything."""
    if base is None:
        return None
    d = os.path.dirname(path) or "."
    try:
        run = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, timeout=15)
        merge_base = run("merge-base", base, "HEAD").stdout.strip() or base
        out = run("diff", "-U0", merge_base, "--", os.path.abspath(path))
        if out.returncode != 0:
            return None
    except Exception:
        return None
    changed = set()
    for line in out.stdout.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            changed.update(range(start, start + count))
    return changed


def comment_runs(lines, pfx):
    """Consecutive comment lines. Module docs (//! or #!) are exempt: long explanations go there."""
    runs, i, n = [], 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith(pfx + "!") or s.startswith("#!"):
            i += 1
            continue
        if s.startswith(pfx):
            j = i
            while j < n and lines[j].strip().startswith(pfx) and not lines[j].strip().startswith(pfx + "!"):
                j += 1
            runs.append((i, j)); i = j
        elif s.startswith("/*"):
            j = i
            while j < n and "*/" not in lines[j]:
                j += 1
            runs.append((i, min(j + 1, n))); i = j + 1
        else:
            i += 1
    return runs


def code_span(lines, start, indent):
    """Lines of code a comment documents: to the end of the block it opens, else to the next comment.

    Braces inside a parameter list are types or destructuring, not the body. Counting them
    ends the span at the signature and reports a cap far tighter than the real one.
    """
    count, depth, paren, opened, i = 0, 0, 0, False, start
    while i < len(lines):
        raw = lines[i]; s = raw.strip()
        if not s:
            i += 1; continue
        if s.startswith(("//", "/*", "*", "#")):
            if not opened:
                break
            i += 1; continue
        if len(raw) - len(raw.lstrip()) < indent and opened and depth == 0:
            break
        count += 1
        for ch in raw:
            if ch == "(":
                paren += 1
            elif ch == ")":
                paren = max(0, paren - 1)
            elif paren == 0 and ch == "{":
                depth += 1; opened = True
            elif paren == 0 and ch == "}":
                depth -= 1
        if opened and depth <= 0:
            break
        i += 1
    return count


RUST_FN = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?(default\s+)?(const\s+)?(async\s+)?(unsafe\s+)?(extern\s+\"[^\"]*\"\s+)?fn\s+(\w+)")
TS_FN = re.compile(r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s*\*?\s*(\w+)")
TS_ARROW = re.compile(r"^\s*(export\s+)?(const|let|var)\s+(\w+)\s*(:[^=]+)?=\s*(async\s+)?\([^)]*\)\s*(:[^=]+)?=>\s*\{")
TS_METHOD = re.compile(r"^\s*(public|private|protected|static|async|get|set|\s)*?(\w+)\s*\([^;]*\)\s*(:\s*[^{;]+)?\{\s*$")
PY_FN = re.compile(r"^\s*(async\s+)?def\s+(\w+)")
NOT_FN = {"if", "for", "while", "switch", "catch", "do", "else", "return", "match", "loop",
          "unsafe", "impl", "struct", "enum", "trait", "function", "constructor"}
BINDING = re.compile(r"^\s*(let\s+(mut\s+)?|const\s+|var\s+)")


def fn_starts(lines, ext):
    for idx, raw in enumerate(lines):
        if raw.strip().startswith(("//", "*", "#")):
            continue
        name = None
        if ext == ".rs":
            m = RUST_FN.match(raw)
            name = m.group(8) if m else None
        elif ext == ".py":
            m = PY_FN.match(raw)
            name = m.group(2) if m else None
        else:
            for pat, grp in ((TS_FN, 4), (TS_ARROW, 3), (TS_METHOD, 2)):
                m = pat.match(raw)
                if m and m.group(grp) not in NOT_FN:
                    name = m.group(grp); break
        if name:
            yield idx, name


def fn_length(lines, start):
    depth, opened = 0, False
    for i in range(start, len(lines)):
        raw = lines[i]
        o, c = raw.count("{"), raw.count("}")
        depth += o - c
        if o:
            opened = True
        if opened and depth <= 0:
            return i - start + 1
        if not opened and raw.rstrip().endswith(";"):
            return 0
    return 0


def declaration_comments(lines, start, end, pfx):
    """Comment runs sitting directly on a variable binding. One is ordinary; several mean bad names."""
    count, i = 0, start
    while i < end:
        if lines[i].strip().startswith(pfx) and not lines[i].strip().startswith(pfx + "!"):
            j = i
            while j < end and lines[j].strip().startswith(pfx):
                j += 1
            if j < end and BINDING.match(lines[j]):
                count += 1
            i = j
        else:
            i += 1
    return count


def audit(path, base, show_detail=True):
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return 0
    pfx, ext = line_prefix(path), "." + path.rsplit(".", 1)[-1]
    changed = changed_lines(path, base)
    touched = lambda lo, hi: changed is None or any(n in changed for n in range(lo, hi + 1))
    found = 0

    for s, e in comment_runs(lines, pfx):
        length = e - s
        if length <= 2 or not touched(s + 1, e):
            continue
        if any(ALLOW_VERBOSE.search(lines[k]) for k in range(s, e)):
            continue    # deliberate exception, stated inline and greppable
        span = code_span(lines, e, len(lines[s]) - len(lines[s].lstrip()))
        if span and length > COMMENT_TARGET and length * 2 > span:
            found += 1
            if show_detail:
                print(f"===== {path}:{s + 1}  {length} lines on {span} code -> MAX {max(COMMENT_TARGET, span // 2)} LINES")
                for i in range(s, min(e + 3, len(lines))):
                    print(f"{i + 1:6d}| {lines[i]}")

    for idx, name in fn_starts(lines, ext):
        n = fn_length(lines, idx)
        if n < 20 or not touched(idx + 1, idx + n):
            continue
        if n > MAX_FN_LINES and show_detail:
            print(f"===== {path}:{idx + 1}  fn {name} is {n} lines (budget {MAX_FN_LINES})")
        d = declaration_comments(lines, idx, idx + n, pfx)
        if d > MAX_DECL_COMMENTS and show_detail:
            print(f"===== {path}:{idx + 1}  fn {name} has {d} comments explaining a variable name - rename instead")
    return found


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--base", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    if not a.files:
        print(__doc__); return 0
    base = None if a.all else (a.base or default_base())
    total = 0
    for f in a.files:
        if not f.endswith(EXTS) or SKIP.search(f):
            continue
        n = audit(f, base, show_detail=not a.summary)
        total += n
        if a.summary and n:
            print(f"{n:5d}  {f}")
    if a.summary:
        print(f"--- {total} findings")
    return 0


def default_base():
    for ref in ("origin/main", "origin/master", "main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", ref], capture_output=True).returncode == 0:
            return ref
    return None


if __name__ == "__main__":
    sys.exit(main())
