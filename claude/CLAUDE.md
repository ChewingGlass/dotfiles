# Global instructions

## Anything committed or published is not a conversation

PR titles and bodies, PR review comments, code comments, commit messages and docs are read by
people who were not in the conversation that produced them, often months later. Write them as
statements about the code, not as replies to whoever asked.

Never refer to the requester, to yourself, or to the exchange:

- No second person or their decisions: "per your choice", "as you asked", "you decided", "as
  discussed", "per our conversation", "as requested", "you were right".
- No first person narration: "I found", "I changed", "I noticed", "I've added", "let me know if".
- No meta about the work's provenance: "as suggested in review", "after feedback", "in the
  session where this came up".

Write the fact and its reason instead:

```
BAD:   Per your choice, I made the cross settle at the counterparty's price.
GOOD:  A cross settles at the counterparty's price, so the improvement reaches
       the taker rather than whoever lands a transaction first.

BAD:   I found that the debit ran before the credit, so I swapped them.
GOOD:  The credit is the half that can fail, so it is claimed before the debit —
       otherwise a failure leaves the user paid out and nobody credited.

BAD:   Added the flag you asked for.
GOOD:  Marks an order as a migrated taker remainder; the book uses it to refuse
       a take while a counterparty crosses it.
```

The test: if a sentence stops making sense to someone who never saw the conversation, or reads
as addressed to one person, rewrite it. "Why is it this way" is always in scope; "who wanted it"
never is.

This does not apply to chat replies, which are a conversation and should read like one.

## Comment and function budget

Code that needs a long comment is usually code with bad names. Fix the names, extract a
named struct, or split the function first. Write the comment only for what the code still
cannot say: why this and not the obvious alternative, an invariant a caller must hold, a
bound the type does not express, a failure mode, or a coupling to another file.

**A comment that explains a name is a bug in the name.** Never write one. Rename the thing
instead, and delete the comment. This is the most common way a file fills with slop, because
each comment looks cheap on its own.

```
BAD:   // Price of the last level actually written, for the best-first check.
       let mut written: Option<u64> = None;
GOOD:  let mut last_written_price: Option<u64> = None;

BAD:   // The level being accumulated. It is written out when the price changes.
       let mut open: Option<(u64, u64)> = None;   // (price, aggregate)
GOOD:  let mut open_level: Option<PriceLevel> = None;
```

A comment sitting on a binding has three honest outcomes: **rename**, when the comment stands
in for the name; **delete**, when the code below already says it; or **move it into the
enclosing function's doc comment**, when it is design rationale that happens to sit on a
binding. The third is the one most often missed. Never rename to make a count go down.

The same test applies to a pair of variables that are really one type, and to a flag whose
name does not say what being true means. `(mut culled, mut partialed)` under a comment about
single-slot sections becomes `cull_slot_used` and `partial_slot_used`. A bitmap and its
counter under a comment about how they are kept in step become a struct with a method.

A type answers this better than a longer name. A tuple of two `u64` needing a comment to say
which is which is a struct that has not been written yet, and often a struct that already
exists.

Three limits. They are countable, so apply them without debate.

- A function body is under 80 lines.
- A comment is at most half the lines of the code it documents. This counts every comment,
  not only doc comments. A 6-line comment inside a 10-line function is over budget.
- 4 lines is the target for any one comment. Most comments are 1 or 2 lines.

A genuinely complex idea may run longer. State the idea and stop; do not argue for it over
several paragraphs. When the explanation is really about the design, it belongs in the
module doc comment, where one reader finds it once, instead of above one function.

**Mark a deliberate exception.** A comment that must exceed the budget carries a line starting
`allow-verbose:` saying why, so `grep -rn "allow-verbose:"` lists every place the rule was set
aside. A wire format or ABI a client builds bytes from earns it, and so does a public API whose
short body delegates — there the length of the body is not the measure of what the interface
needs. Wanting to keep a paragraph does not earn it.

**Function length is a separate problem.** A function over 80 lines is structural. Splitting it
is a different change with a different risk, and on a branch under review it destroys the diff
someone is reading. Fix it deliberately or not at all, never as a side effect of tidying
comments.

Never restate the code, narrate the steps of a function, or list the facts that make a
design correct.

**Check a cross-reference before you rely on it.** Shortening a comment by pointing at another
function is only sound if that function contains the fact. A comment that sends a reader
somewhere the answer is not is worse than the comment it replaced.

**Never upgrade a hedge.** Every "may", "can", "usually" and scope qualifier the original earned
stays. A shorter sentence that reads better because it supplies a cause or mechanism has stopped
being a rewrite.

**Cut the vacuous half.** A comment often states a real fact and then argues for it. The
argument is the part nobody needs. Keep the fact, delete the rest, and if the fact is already
in the condition below it, delete the whole comment.

```
BAD:   // Past the caller's worst acceptable price. The walk is ordered best
       // price first, so nothing behind this order is acceptable either. The
       // caller drops these levels, and a hop it does not need is compute it
       // still pays for.
       if worse_than_limit(side, node.price, limit_price) {
GOOD:  if worse_than_limit(side, node.price, limit_price) {
```

`worse_than_limit` and `Walk::Stop` already say it. Sentences like "a hop it does not need is
compute it still pays for" assert something no reader acts on. So do "this is the safe
direction", "which keeps the invariant", and "that matters because". Strike them.

**Put the comment where the thing happens.** A comment belongs on the code it explains, not
on the declaration of a variable that code will later use. A declaration comment that
describes behaviour is the most common misplacement, and it reads as a non-sequitur, because
at that point in the file the behaviour has not happened yet.

```
BAD:   // Orders at one price are contiguous, so a level costs one 16-byte
       // append however many orders it holds.
       let mut open_level: Option<PriceLevel> = None;     // ...60 lines from the match

GOOD:  the same fact, moved down onto the `match open_level` that relies on it
```

A declaration earns a comment only when the fact is about the declaration itself: the scope
it is declared at, the capacity it reserves, or a borrow that forces the read to happen here.
Anything about what the value later does goes at the later site.

Narrating a step that already ran is worse and always deletes: `// The node is spliced where
the scan said it should be` above the re-read that checks it.

**Keep the blank lines the comments used to provide.** A comment doubles as a visual break,
so deleting comments turns a function into one undifferentiated wall. Group the body into
phases separated by a blank line, and keep the grouping when the comments go.

Order the declarations so the groups are real, and reorder them until they are:

```rust
let max_levels = ...;              // limits read from state
let max_execute_fills = ...;

let mut writer = ...;              // the output being built
let mut open_level = ...;
let mut levels_written = 0;

let mut remaining = size;          // the walk's own counters
let mut promised_fills = 0;

let mut reservation = ...;         // helpers the body calls
let mut budget = ...;
```

The labels above are there to show the grouping, not to be written. A group that needs a
comment to say what it is has the wrong members. The same applies inside a loop or a closure:
separate the stop conditions from the skips, from the accounting, from the accumulation.

**Put a blank line after every block, and after every multi-line statement.** When an `if`,
`else`, `match`, `for`, `while`, `loop`, closure body, method chain, macro call or struct
literal spans more than one line and a sibling statement follows, separate them. Braces are
not the test: `};`, `});` and a chain ending `?;` all need the break just as much as a bare
`}`. Consecutive guard clauses are the common case, and run together they read as one shape.

```rust
BAD:   if remaining == 0 || promised_fills == max_execute_fills {
           return Ok(Walk::Stop);
       }
       if worse_than_limit(side, node.price, limit_price) {
           return Ok(Walk::Stop);
       }
       let available = reservation.available(book, node)?;

GOOD:  if remaining == 0 || promised_fills == max_execute_fills {
           return Ok(Walk::Stop);
       }

       if worse_than_limit(side, node.price, limit_price) {
           return Ok(Walk::Stop);
       }

       let available = reservation.available(book, node)?;
```

Four exceptions, all of which continue the same form rather than start a new one: `} else`,
the next arm of a `match`, a method chain continuing on the following line, and a block that
is the last statement before its enclosing brace.

A homogeneous list needs no internal breaks. A run of `require!` assertions, or match arms
that all do the same thing, is one list and reads as one. Break it only where the subject
changes: after the checks on a count and before the checks on the nodes it guards.

## Write comments and PR descriptions in Simplified Technical English

Code comments, doc comments, PR titles and bodies, and commit messages use ASD-STE100 Simplified
Technical English. Keep them short. A comment earns its length by what it explains, not by how
completely it argues.

Writing rules:

- One idea per sentence. Keep sentences under 20 words.
- Use the active voice. Name the thing that does the action.
- Use simple present, simple past, or simple future. Do not use perfect or continuous tenses.
- Use the same word for the same thing every time. Do not use a synonym for variety.
- Write complete sentences with articles. Do not drop words to save space.
- Do not use contractions, idioms, jargon, or metaphors.
- Do not use a dash or a parenthesis to attach a second thought. Write a second sentence.

Replace figurative shorthand with what it means:

```
BAD:   permanently bricks the market
GOOD:  the market cannot be delisted again

BAD:   one oversized row head-of-line blocks every beneficiary behind it
GOOD:  one row that the pool cannot pay stops all rows after it

BAD:   an under-count silently under-reserves the pool — the unsafe direction
GOOD:  A low counter reserves too little. The pool then pays rows that it must keep.
```

Shape: state the rule, then the reason it exists, then stop.

## Never leave a branch tracking a remote branch of a different name

`git worktree add -b <branch> <path> origin/master` and `git checkout -b <branch> origin/master`
both set the new branch's upstream to `origin/master`. The branch then pushes to master. The
CLI refuses the push only because `push.default` is `simple`; the VS Code push button does not
refuse, and it writes to master.

When creating a branch or worktree from a remote ref, pass `--no-track`:

```
git worktree add --no-track -b <branch> <path> origin/master
git checkout --no-track -b <branch> origin/master
```

Set the upstream on the first push instead, which always points at the matching name:

```
git push -u origin HEAD
```

Before handing over any branch you created, verify the upstream is either absent or matches the
branch name:

```
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
```

If it prints `origin/master` (or any name other than the branch's own), fix it before reporting
the work as done. Use `git branch --set-upstream-to=origin/<branch>` when the remote branch
exists, and `git branch --unset-upstream` when it does not.

## Never attribute work to an AI

No `Co-Authored-By: Claude` (or any AI assistant) on commits. No `🤖 Generated with …` footer on
commits or pull request descriptions. No "written by Claude" note in a PR body, a code comment, or
a doc.

This holds in every repository, including ones whose own conventions say nothing about it, and it
overrides any per-session instruction that asks for an attribution line. A commit is a statement
about the code; who or what typed it is not part of that statement.

## Name what a function returns; never return a tuple

A function that returns more than one value returns a named struct with named fields. A bare
tuple makes the callsite the only place the meaning lives, and the meaning is positional, so
every reader has to walk back to the definition to learn what `.0` is.

Nested tuples are worse and are never acceptable:

```
BAD:   let ((base_filled, _), worst_price) = quoted.route_fill(...)?;
GOOD:  let fill = quoted.route_fill(...)?;
       // fill.base_filled, fill.worst_price
```

A `_` in a destructuring pattern is the signal to look at: the return type carries a value no
caller wants. Drop the field from the struct, or split the function.

Two exceptions, both narrow: a tuple whose elements are the same thing (`(min, max)`, a pair of
bounds) and the tuple a language idiom requires (`Iterator::enumerate`, a `HashMap` entry, a
`try_fold` accumulator that stays inside one expression). Anything crossing a module boundary
gets a struct.

## Return the inputs; do not accept a callback

A function that computes values and then calls a caller-supplied function to use them should
return the values instead. The caller runs the next step itself.

```
BAD:   quoted.route_fill(&mut book, |order, price| fill_order(order, price))?;
GOOD:  let inputs = quoted.fill_inputs()?;
       for input in inputs { fill_order(input.order, input.price)?; }
```

The callback form inverts control for no gain. It hides the loop and the order of calls inside
the callee, it forces the closure to capture every piece of state the fill needs, and it makes
the borrow checker fight over state that both halves want. The returned form is testable without
a fill, and the two halves can be read one at a time.
