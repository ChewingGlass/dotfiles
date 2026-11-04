#!/usr/bin/env python3
"""Insert a blank line after every block and multi-line statement.

    space-blocks.py <file>...                 # only lines changed vs the default branch
    space-blocks.py --all <file>...           # the whole file
    space-blocks.py --base <ref> <file>...

Idempotent: a second run inserts nothing. Safe to re-run at the end of a parallel pass to
repair agents that stripped spacing believing it was foreign.

Skips four cases that continue a form rather than start one: `} else`, the next match arm, a
method chain, and a closer followed by more of the same statement. Also skips a homogeneous
list (consecutive statements with the same leading token) and never splits an attribute from
the item it annotates.
"""
import argparse, os, re, subprocess, sys

CLOSERS = ("}", ")", "]")
ATTR = re.compile(r"^\s*(#\[|#!\[|@)")


def default_base():
    for ref in ("origin/main", "origin/master", "main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", ref], capture_output=True).returncode == 0:
            return ref
    return None


def changed_lines(path, base):
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
    s = set()
    for line in out.stdout.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            a, c = int(m.group(1)), int(m.group(2) or 1)
            s.update(range(a, a + c))
    return s


def head_token(lines, i, indent):
    """First token of the statement whose closing delimiter sits on line i."""
    for k in range(i - 1, -1, -1):
        raw = lines[k]
        if not raw.strip():
            continue
        if len(raw) - len(raw.lstrip()) == indent and raw.strip()[0] not in CLOSERS:
            return re.split(r"[\s(<!{:;]", raw.strip(), maxsplit=1)[0]
    return None


def process(path, base):
    lines = open(path, encoding="utf-8").read().split("\n")
    changed = changed_lines(path, base)
    out, added = [], 0
    for i, line in enumerate(lines):
        out.append(line)
        s = line.strip()
        if not s or s[0] not in CLOSERS:
            continue
        if s.endswith(")]") or ATTR.match(s):
            continue                                   # a multi-line attribute
        if s.endswith(","):
            continue                                   # an element of a list, not a statement
        j = i + 1
        if j >= len(lines):
            continue
        nxt = lines[j]
        t = nxt.strip()
        if not t or t[0] in "})],.;:" or t.startswith("else") or ATTR.match(nxt) or "=>" in t:
            continue
        indent = len(line) - len(line.lstrip())
        if indent != len(nxt) - len(nxt.lstrip()):
            continue                                   # not a sibling statement
        if changed is not None and not (i + 1 in changed or j + 1 in changed):
            continue
        h = head_token(lines, i, indent)
        if h and t.startswith(h):
            continue                                   # homogeneous list
        out.append("")
        added += 1
    if added:
        open(path, "w", encoding="utf-8").write("\n".join(out))
    return added


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--base", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    if not a.files:
        print(__doc__)
        return 0
    base = None if a.all else (a.base or default_base())
    total = 0
    for f in a.files:
        try:
            n = process(f, base)
        except Exception as e:
            print(f"skip {f}: {e}")
            continue
        if n:
            total += n
            print(f"{n:5d}  {f}")
    print(f"--- inserted {total} blank lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
