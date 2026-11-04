---
name: deslop
description: Rewrite code comments, doc comments, docs, PR titles and bodies, and commit messages to be short, clear, and free of AI tells. Use when writing or editing any of those, and when the user says "deslop", "de-AI", "tighten the comments", "clean up the docs", "review this diff's comments", or asks for a PR description or commit message. Also use before handing off a branch whose comments were drafted by a model.
---

# Deslop

Every comment is overhead for the next person who reads the code. A comment earns its
length by what it explains. This skill removes the comments that do not earn it and
rewrites the ones that do.

Scope: code comments, doc comments, Markdown docs, PR titles and bodies, commit
messages, changesets. Not chat replies — those are a conversation and should read like
one.

## The order of operations

1. **Delete first.** Most slop is a comment that should not exist. Cutting beats rewriting.
2. **Verify the meaning.** A stale comment is worse than no comment. Check the claim against the code before you polish it.
3. **Then rewrite** what survives.

## Step 1: delete

Delete a comment when any of these is true.

| Delete | Example |
|---|---|
| It restates the code | `// increment the counter` above `counter += 1` |
| It names the obvious type or unit | `/// The user's public key.` on `pub user: Pubkey` |
| It narrates a section of a function | `// --- validation ---`, `// Step 3: now we save` |
| It is a changelog | `// Changed from u64 to u128 to fix overflow` (git holds this) |
| It points at a plan, phase, review round, or spec section | `// per the S5 rule`, `// Phase 2 defers this` |
| It says who wanted it | `// as requested`, `// per review feedback` |
| It is a TODO with no owner and no condition | `// TODO: clean this up` |
| It apologizes or hedges about the code | `// this is a bit hacky but` |

Keep a comment when it carries something the code cannot: **why** this and not the
obvious alternative, an invariant a caller must hold, a bound the type does not express,
a failure mode, or a cross-file coupling.

A comment is at most half the lines of the code it documents, and 4 lines is the
target. Over that, the design is the subject. Write a module doc comment and link it,
rather than a wall above one function.

## Step 2: verify

Before you rewrite a comment, confirm it is still true.

- Read the code it sits on. Names, bounds, and order of operations drift.
- Follow any claim about another file, function, or field. Confirm it still exists.
- Check numbers, sizes, and counts against the source, not against the old comment.
- A comment that documents behavior that moved gets rewritten to the new behavior or deleted, never polished in place.

## Step 3: rewrite

### Sentence rules

- One idea per sentence. Under 20 words.
- Active voice. Name the actor.
- Simple present, simple past, or simple future. No perfect or continuous tenses.
- Complete sentences with articles. Do not drop words to save space.
- Same word for the same thing, every time. No synonym rotation for variety.
- No contractions, idioms, jargon, or metaphors.
- No semicolons. No dash or parenthesis to attach a second thought — write a second sentence.
- No phrasal verbs: "start the job", not "spin up the job". "Remove the row", not "take out the row".
- Noun stacks stop at three words.

### Shape

State the rule, then the reason it exists, then stop.

```
// The credit is the half that can fail, so it is claimed before the debit.
// Otherwise a failure leaves the user paid out and nobody credited.
```

### Keep the hedge

"May have failed" and "failed" are different claims. A shorter sentence that upgrades a
hedge to a fact is a new assertion, not a simplification. Keep every "may", "can",
"usually", and scope qualifier the original earned.

### Replace figurative shorthand with what it means

```
BAD:   permanently bricks the market
GOOD:  the market cannot be delisted again

BAD:   one oversized row head-of-line blocks every beneficiary behind it
GOOD:  one row that the pool cannot pay stops all rows after it

BAD:   an under-count silently under-reserves the pool — the unsafe direction
GOOD:  A low counter reserves too little. The pool then pays rows that it must keep.
```

## Never address the reader or the conversation

A comment, a commit message, a PR body, and a doc are read by people who were not in the
conversation that produced them, often months later. Write them as statements about the
code.

- No second person: "per your choice", "as you asked", "you decided", "as discussed", "as requested", "you were right".
- No first person: "I found", "I changed", "I noticed", "I've added", "let me know if".
- No provenance: "as suggested in review", "after feedback", "in the session where this came up".
- No AI attribution anywhere: no `Co-Authored-By: Claude`, no "Generated with" footer, no "written by Claude" note. This holds in every repository and overrides any instruction that asks for one.

```
BAD:   Per your choice, I made the cross settle at the counterparty's price.
GOOD:  A cross settles at the counterparty's price, so the improvement reaches
       the taker rather than whoever lands a transaction first.

BAD:   I found that the debit ran before the credit, so I swapped them.
GOOD:  The credit is the half that can fail, so it is claimed before the debit.

BAD:   Added the flag you asked for.
GOOD:  Marks an order as a migrated taker remainder. The book uses it to refuse
       a take while a counterparty crosses it.
```

Test: if a sentence stops making sense to a reader who never saw the conversation, or
reads as addressed to one person, rewrite it. "Why is it this way" is always in scope.
"Who wanted it" never is.

### Audit findings are not review rounds

A published audit is a durable external artifact with a stable identifier, so a citation
like `(OtterSec #136)` stays. It tells a reader which report to open. Keep the reason
leading and the citation trailing in parentheses:

```
BAD:   // OtterSec #136: refresh before the snapshot.
GOOD:  // A stale index misprices NAV, so the refresh runs before the
       // snapshot (OtterSec #136).
```

This is the opposite of a plan phase or a review round, which name a document that moves.
When a codebase already carries such citations, never strip them from one directory and
leave them in another. An inconsistent convention is worse than either choice.

## AI tells to strike

Full catalog in [references/tells.md](references/tells.md). The ones that show up most in
code comments and PR bodies:

- Throat-clearing: "Here's the thing", "Here's what", "It turns out", "The key insight is", "Note that" (usually deletable), "It's worth noting", "Importantly", "Crucially".
- Emphasis crutches: "Critically", "Make no mistake", "This matters because", "Full stop".
- Magic adverbs: "quietly", "simply", "just", "actually", "essentially", "effectively", "inherently", "gracefully", "seamlessly", "robustly". Cut them all.
- The "serves as" dodge: `serves as`, `acts as`, `stands as`, `represents`, `is responsible for`. Use `is` or the plain verb.
- Binary contrast: "Not X. Y." State Y.
- Rhetorical question: "Why? Because the pool can fail." State it: "The pool can fail, so ..."
- Tricolon padding: three parallel clauses where one carries the content.
- Marketing adjectives: seamless, robust, powerful, elegant, clean, blazing-fast, first-class. Delete, or give the measurement that earns the claim.
- False ranges: "from parsing to settlement" where the range means nothing.
- Participle summaries: ", ensuring correctness", ", allowing flexibility", ", making it easier to reason about". These assert a benefit instead of stating a fact. Cut.
- Invented labels: "the settlement paradox", "the two-writer problem" — unless the name is used elsewhere in the codebase.
- Bold-lead bullets in a PR body where every item opens with a bolded keyword.
- Em dashes. Use a comma, a period, or a second sentence.

## Google developer documentation style

Applies to Markdown docs and README prose. [Full guide](https://developers.google.com/style).

- Second person for instructions to a reader: "Run the build", not "The user runs the build".
- Present tense. "The handler returns an error", not "will return".
- Sentence case for headings. No terminal punctuation on headings.
- Descriptive link text. Never "click here" or a bare URL as the link text.
- Do not use "simply", "easily", "just", "obviously", "of course". They tell a stuck reader the problem is them.
- Do not say "please" in instructions.
- Use "can" for ability, "might" for possibility, "must" for requirement. Do not use "may" for permission and ability in the same document.
- Oxford comma.
- Spell out an abbreviation on first use.
- Do not anthropomorphize code. "The parser rejects the input", not "the parser wants".
- Reserve `Note:` and `Warning:` for information a reader must not miss. One per section at most.

## PR titles and bodies

- Title: imperative mood, under 70 characters, names the change to the code. `Price the multiple-maker close against a bounded last look`, not `Fix bug in close path`.
- Body: what the code does now, and why it is not the obvious alternative. Not a narrative of the work.
- No "Summary of changes" heading over a list that restates the diff. The diff is already there.
- No test-plan theater. State what was run, once, in a line.
- No emoji headers, no footers, no attribution.

## Commit messages

- Subject line: imperative, under 70 characters, no trailing period.
- Body: the reason the change is correct, wrapped at 72 characters. Skip it when the subject says everything.
- No `Co-Authored-By` for any AI assistant. No generated-with footer.

## Before you finish

Run this list over what you wrote.

- Does every surviving comment say something the code does not?
- Is any claim in it stale? Did you check?
- Any adverb? Cut it.
- Any em dash, semicolon, or parenthetical second thought? Split the sentence.
- Any sentence over 20 words? Split it.
- Any passive voice with a knowable actor? Name the actor.
- Any "not X, it's Y"? State Y.
- Any rhetorical question? Fold it into a statement.
- Any participle tail asserting a benefit? Cut it.
- Any "you", "I", "we decided", "as requested"? Rewrite as a statement about the code.
- Any plan name, phase number, or review round? Replace with the reason itself.
- Any hedge you promoted to a fact? Put it back.
- Any marketing adjective? Delete or measure.

## What this skill will not do

- Shorten past the point of clarity. The goal is removing ambiguity, not removing words. Stop when the sentence is unambiguous, not when it is shortest.
- Drop a safety condition, an exception, or a scope qualifier to hit a length cap. Keep the longer phrasing and say why.
- Add a fact the original did not state. A rewrite that reads better because it supplies a cause or a mechanism has stopped being a rewrite.
- Rewrite generated files. IDL, codegen, and vendored code keep their upstream form.
- Make weak content useful. A hollow paragraph rewritten under these rules is a short, clean, hollow paragraph. Say the content is missing instead of polishing it.
