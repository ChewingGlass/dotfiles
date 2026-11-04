#!/usr/bin/env python3
"""Report over-long functions and over-budget comments in a file that was just edited.

Reads a PostToolUse payload on stdin. Writes findings to stderr and exits 2, which
shows them to the model without reverting the edit.
"""

import json
import os
import re
import subprocess
import sys

EXTS = (".rs", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".swift", ".c", ".h", ".cpp")
SKIP = re.compile(
    r"(^|/)(node_modules|target|dist|build|vendor|\.next|fuzz/corpus)/"
    r"|/idl/|_idl\.rs$|\.generated\.|\.d\.ts$|_pb\.|\.min\.js$"
)

MAX_FN_LINES = 80
COMMENT_TARGET = 4
ALLOW_VERBOSE = re.compile(r"allow-verbose:")
MAX_ANNOTATED_BINDINGS = 3

RUST_FN = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?(default\s+)?(const\s+)?(async\s+)?(unsafe\s+)?(extern\s+\"[^\"]*\"\s+)?fn\s+(\w+)")
TS_FN = re.compile(r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s*\*?\s*(\w+)")
TS_ARROW = re.compile(r"^\s*(export\s+)?(const|let|var)\s+(\w+)\s*(:[^=]+)?=\s*(async\s+)?\([^)]*\)\s*(:[^=]+)?=>\s*\{")
TS_METHOD = re.compile(r"^\s*(public|private|protected|static|async|get|set|\s)*?(\w+)\s*\([^;]*\)\s*(:\s*[^{;]+)?\{\s*$")
NOT_FN = {"if", "for", "while", "switch", "catch", "do", "else", "return", "match", "loop", "unsafe", "impl", "struct", "enum", "trait", "function", "constructor"}


def is_comment(line):
    s = line.strip()
    return s.startswith("//") or s.startswith("/*") or s.startswith("*") or s.startswith("#[") is False and s.startswith("*/")


def comment_runs(lines):
    """Yield (start, end_exclusive) for each run of comment lines. Module docs are exempt."""
    runs = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith("//!") or s.startswith("#!"):
            i += 1
            continue
        if s.startswith("//"):
            j = i
            while j < n and lines[j].strip().startswith("//") and not lines[j].strip().startswith("//!"):
                j += 1
            runs.append((i, j))
            i = j
        elif s.startswith("/*"):
            j = i
            while j < n and "*/" not in lines[j]:
                j += 1
            runs.append((i, min(j + 1, n)))
            i = j + 1
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


def fn_starts(lines, ext):
    for idx, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("//") or s.startswith("*"):
            continue
        name = None
        if ext == ".rs":
            m = RUST_FN.match(raw)
            if m:
                name = m.group(8)
        else:
            for pat, grp in ((TS_FN, 4), (TS_ARROW, 3), (TS_METHOD, 2)):
                m = pat.match(raw)
                if m and m.group(grp) not in NOT_FN:
                    name = m.group(grp)
                    break
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
            return 0  # a trait signature with no body
    return 0


def changed_lines(path):
    """1-based lines this working tree changed against HEAD. None means treat every line as new."""
    d = os.path.dirname(path) or "."
    try:
        run = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, timeout=10)
        if run("rev-parse", "--show-toplevel").returncode != 0:
            return None
        if run("ls-files", "--error-unmatch", path).returncode != 0:
            return None  # untracked: the whole file is new
        out = run("diff", "-U0", "HEAD", "--", path)
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


def touched(changed, lo, hi):
    return changed is None or any(n in changed for n in range(lo, hi + 1))


BINDING = re.compile(r"^\s*(let\s+(mut\s+)?|const\s+|var\s+|(pub(\([^)]*\))?\s+)?(let|const)\s)")


def annotated_bindings(lines, start, end):
    """Count comment runs inside [start, end) that sit directly on a variable binding.

    A comment explaining a name is a naming problem. One is ordinary; several in one
    function body mean the names are carrying nothing.
    """
    count = 0
    i = start
    while i < end:
        s = lines[i].strip()
        if s.startswith("//") and not s.startswith("//!"):
            j = i
            while j < end and lines[j].strip().startswith("//"):
                j += 1
            if j < end and BINDING.match(lines[j]):
                count += 1
            i = j
        else:
            i += 1
    return count


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(EXTS) or SKIP.search(path):
        return 0
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return 0

    ext = "." + path.rsplit(".", 1)[-1]
    changed = changed_lines(path)
    findings = []

    for start, end in comment_runs(lines):
        length = end - start
        if length <= 2 or not touched(changed, start + 1, end):
            continue
        indent = len(lines[start]) - len(lines[start].lstrip())
        if any(ALLOW_VERBOSE.search(lines[k]) for k in range(start, end)):
            continue    # deliberate exception, stated inline and greppable
        span = code_span(lines, end, indent)
        if span and length > COMMENT_TARGET and length * 2 > span:
            findings.append(
                f"{path}:{start + 1}: {length}-line comment on {span} lines of code "
                f"(budget: half the code, target 4 lines)"
            )

    for idx, name in fn_starts(lines, ext):
        if not touched(changed, idx + 1, idx + 1):
            continue
        length = fn_length(lines, idx)
        if length > MAX_FN_LINES:
            findings.append(f"{path}:{idx + 1}: fn {name} is {length} lines (budget: 80)")
        annotated = annotated_bindings(lines, idx, idx + max(length, 1))
        if annotated > MAX_ANNOTATED_BINDINGS:
            findings.append(
                f"{path}:{idx + 1}: fn {name} has {annotated} comments explaining a "
                f"variable name (budget: {MAX_ANNOTATED_BINDINGS}) - rename instead"
            )

    if not findings:
        return 0

    sys.stderr.write(
        "Comment and function budget (see ~/.claude/CLAUDE.md):\n  "
        + "\n  ".join(findings[:12])
        + (f"\n  ... and {len(findings) - 12} more" if len(findings) > 12 else "")
        + "\n\nCut the comment to what the code cannot say, or improve the names so it is "
          "not needed. Move a long explanation to the module doc comment. Split a long "
          "function. If the length is deliberate, say why on the first line and move on.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
