---
name: deslop-comments
description: Cut bloated code comments down to what earns its length, and keep the blank-line structure that goes with them. Use when writing or reviewing comments, when a file or diff reads comment-heavy, and when the user says "deslop", "de-AI", "tighten the comments", "the comments are too long", or asks to clean up a branch before handing it off. Includes tools that find violations with an exact per-comment line budget, so rewriting is measured rather than judged.
---

# Deslop comments

Long comments do not come from one bad decision. Each looks cheap on its own, and a file
reaches 30% comments without anyone choosing that. A rule you can count survives a long
session; a rule you have to feel does not.

**Run the tool first. Do not eyeball this.**

```bash
python3 <skill>/tools/find-violations.py <file>...        # vs merge-base with the default branch
python3 <skill>/tools/find-violations.py --all <file>...  # ignore git, audit everything
python3 <skill>/tools/find-violations.py --summary <dir-glob>
```

Every finding prints its own cap: `-> MAX N LINES`. Rewrite to that number. Do not estimate
it — an estimate overshoots, and the overshoot is invisible until you re-run.

**Re-run after every batch.** Rewriting shifts line numbers, which moves other blocks into the
changed-line window. Findings that were not there the first time appear. Keep going until it
reports nothing.

## The budget

- A comment block is at most **half the lines of the code it documents**.
- A block of **4 lines or fewer never trips** the ratio, so short helpers are not nagged.
- A function body is under **80 lines**.
- More than **3 comments explaining a variable name** in one function is a naming problem,
  not a commenting problem. This one is a prompt to look, not a verdict: the check fires on
  any comment sitting directly above a binding, and a comment explaining an *algorithm step*
  legitimately sits there too. Never rename to dodge the count. There are three honest
  outcomes: rename, when the comment stands in for the name; delete, when the code below
  already says it; or **move it into the enclosing function's doc comment**, when it is
  design rationale that happens to sit on a binding. The third is the one people miss.

## The four cuts

**1. A comment that explains a name is a bug in the name.** Rename the thing and delete the
comment. This is the most common source of bloat, because each one looks harmless.

```
BAD:   // Price of the last level actually written, for the best-first check.
       let mut written: Option<u64> = None;
GOOD:  let mut last_written_price: Option<u64> = None;

BAD:   // The level being accumulated, written out when the price changes.
       let mut open: Option<(u64, u64)> = None;   // (price, aggregate)
GOOD:  let mut open_level: Option<PriceLevel> = None;
```

A tuple that needs a comment saying which field is which is a struct that has not been
written yet, and often one that already exists. A pair of variables under one shared comment
is a struct with a method.

**2. Cut the vacuous half.** A comment often states a real fact and then argues for it. Keep
the fact. If the fact is already in the line below, delete the whole comment.

```
BAD:   // Past the caller's worst acceptable price. The walk is ordered best price
       // first, so nothing behind this order is acceptable either. The caller drops
       // these levels, and a hop it does not need is compute it still pays for.
       if worse_than_limit(side, node.price, limit_price) {
GOOD:  if worse_than_limit(side, node.price, limit_price) {
```

Tells: "which keeps the invariant", "this is the safe direction", "that matters because",
"the key insight is". A sentence nobody acts on is not a fact.

**3. Put the comment where the thing happens.** A comment belongs on the code it explains,
not on the declaration of a variable used sixty lines later. On the declaration it reads as a
non-sequitur, because the behaviour has not happened yet.

A declaration earns a comment only when the fact is about the declaration itself: the scope
it is declared at, the capacity it reserves, or a borrow that forces the read to happen here.
Narrating a step that already ran always deletes.

**4. No plan codenames.** Never "per the S5 rule", "Phase 2", "as the spec warns". A reader
has the code, not the plan, and those labels expire. Write the reason itself. A *named,
durable* artifact is fine and stays: a design doc that explains a subsystem, a crate, a type
path, a published audit citation like `(OtterSec #136)`.

## What survives

Why this and not the obvious alternative. An invariant a caller must hold. A bound the type
does not express. A failure mode. A coupling to another file. A measured figure and its unit.
A cross-reference naming the function or formula this mirrors — that is how future drift gets
caught, and it is the last thing to cut.

**Never upgrade a hedge.** "May have failed" and "failed" are different claims. Every "may",
"can", "usually" and scope qualifier the original earned stays. A shorter sentence that reads
better because it supplies a cause or mechanism has stopped being a rewrite and become an
invention.

## Style for what is left

One idea per sentence, under 20 words. Active voice, named actor. Simple tenses. Same word
for the same thing. No contractions, idioms, metaphors, em dashes, semicolons. No
parenthetical second thought — write a second sentence. No "I", "you", "as requested", "we
decided": a comment is read by people who were not in the conversation that produced it.

## Blank lines are part of this

A comment doubles as a visual break, so deleting comments turns a function into one
undifferentiated wall. `tools/space-blocks.py` restores the structure mechanically.

**Put a blank line after every block and every multi-line statement.** Braces are not the
test: `};`, `});` and a chain ending `?;` need the break as much as a bare `}`.

Four exceptions, all continuing the same form rather than starting a new one: `} else`, the
next `match` arm, a method chain continuing on the next line, and a block that is the last
statement before its enclosing brace. A homogeneous list needs no internal breaks — a run of
`require!` assertions is one list; break it only where the subject changes.

Group declarations so the groups are real, and reorder until they are: limits read from
state, then the output being built, then the loop's own counters, then the helpers the body
calls. A group that needs a comment to say what it is has the wrong members.

## The escape hatch, and how to use it honestly

Some comments genuinely exceed the budget. Mark them:

```rust
/// allow-verbose: this is the wire format of a native entrypoint. A client builds the
/// bytes from this comment, and the dispatcher below is short because it delegates, so
/// the length of the body is not the measure of what the interface needs.
```

The tools skip any block containing `allow-verbose:`, and `grep -rn "allow-verbose:"` lists
every place the rule was set aside. An exception that is invisible is how a rule dies; an
exception that is greppable is a decision.

Earns it: a wire format or ABI a client builds bytes from; a public API whose short body
delegates; a derivation a reader cannot reconstruct. Does not earn it: wanting to keep a
paragraph you like.

## Findings that are not comment problems

The tool also reports `fn X is N lines`. That is structural. Splitting a function is a
different change with a different risk, and on a branch under review it destroys the diff an
auditor is reading. Fix it deliberately or not at all — never as a side effect of a comment
pass.

## Before you finish

- Did the tool reach zero, after a re-run?
- Is any surviving claim stale? A wrong comment is worse than none — check it against the code.
- Any cross-reference you kept: does the target actually contain the fact? A doc pointing
  somewhere the fact is not is worse than no doc.
- Any hedge you promoted to a fact? Put it back.
- Any adverb, em dash, rhetorical question, participle tail asserting a benefit? Cut.

## What this will not do

Shorten past clarity. Drop a safety condition to hit a cap. Add a fact the original did not
state. Rewrite generated files, vendored code, or lines a branch did not change. Make weak
content useful — a hollow paragraph rewritten under these rules is a short, clean, hollow
paragraph; say the content is missing instead.

For running this across a whole branch, including the failure modes that cost real time, see
[reference/running-at-scale.md](reference/running-at-scale.md).
