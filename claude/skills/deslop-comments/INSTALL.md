# Installing the hook (optional, recommended)

`tools/hook-comment-budget.py` enforces the budget at write time instead of at review time.
It reports; it never reverts. The edit lands, the model sees the finding while the code is
still in front of it, and fixes it in the same turn.

Copy it somewhere stable and register it as a `PostToolUse` hook:

```jsonc
// ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [{ "type": "command", "command": "/absolute/path/to/hook-comment-budget.py", "timeout": 15 }]
      }
    ]
  }
}
```

The hook scopes findings to lines changed against `HEAD`, so editing a file does not dump
complaints about code you did not touch. `find-violations.py` scopes against the merge-base
with the default branch instead, which is the right basis for a whole-branch pass. Both honour
`allow-verbose:`.

Tunables at the top of either file: `COMMENT_TARGET` (4), `MAX_FN_LINES` (80),
`MAX_DECL_COMMENTS` (3).
