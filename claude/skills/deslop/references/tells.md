# AI tells: full catalog

Load this when a rewrite needs the complete list. The most common tells are already in
SKILL.md.

## Throat-clearing openers

State the content. Delete the runway.

"Here's the thing:", "Here's what", "Here's why", "Here's where it gets interesting",
"Here's the kicker", "Here's the deal", "The key insight is", "The important thing to
understand is", "It turns out", "The real X is", "Let me be clear", "The truth is", "At
its core", "In essence", "Fundamentally", "First and foremost", "To understand X, you
first need to understand Y".

Any "here's what / this / that" construction is runway before the point.

## Emphasis crutches

These add no information.

"Full stop.", "Period.", "Let that sink in.", "Make no mistake", "This matters because",
"Here's why that matters", "Critically,", "Importantly,", "Crucially,", "Notably,", "It
cannot be overstated".

## Pedagogical hand-holding

The reader has the code. They do not need a teacher.

"Let's break this down", "Let's unpack this", "Let's walk through", "Let's dive in",
"Think of it as", "Think of it like", "Imagine a world where", "In other words" (when
the first words were fine), "Put simply", "Essentially what this means is".

## Magic adverbs

Cut every one. If the adverb carries the meaning, the verb is wrong.

quietly, simply, just, really, actually, literally, genuinely, honestly, essentially,
effectively, fundamentally, inherently, inevitably, interestingly, importantly,
crucially, notably, deeply, truly, remarkably, arguably, gracefully, seamlessly,
robustly, safely (when unmeasured), properly, correctly, carefully, cleanly, elegantly.

"Quietly" is the strongest single tell. "The counter quietly drifts" means "the counter
drifts and nothing reports it". Write the second.

## The "serves as" dodge

A pompous substitute for `is` or for the plain verb.

| Avoid | Use |
|---|---|
| serves as | is |
| acts as | is |
| functions as | is |
| stands as | is |
| represents (meaning "is") | is |
| is responsible for | does the thing; name the verb |
| plays a role in | affects, sets, reads |
| is designed to | does |
| aims to | does |
| helps to | does |
| is used to | does |
| provides the ability to | lets |
| performs an analysis of | analyzes |
| provides assistance to | helps |
| makes use of | uses |

## Business jargon

| Avoid | Use |
|---|---|
| leverage (verb) | use |
| utilize | use |
| navigate (a problem) | handle, address |
| landscape | field, situation |
| ecosystem | system |
| paradigm | model, approach |
| synergy | combined effect |
| harness | use |
| streamline | simplify |
| surface (verb) | report, show |
| unlock | allow, let |
| enable (when it means "let") | let |
| deep dive | analysis |
| moving forward | next |
| circle back | revisit |
| game-changer | name the specific gain |

## AI vocabulary

Overrepresented in model output to the point of being a signature.

delve, tapestry, realm, nuanced, holistic, multifaceted, intricate, pivotal, testament,
underscore (as a verb), foster, bolster, myriad, plethora, cornerstone, cutting-edge,
state-of-the-art, best-in-class, first-class, world-class.

## Marketing adjectives

They claim quality instead of showing it. Delete, or replace with the measurement.

seamless, robust, powerful, elegant, clean, intuitive, effortless, blazing-fast,
lightning-fast, comprehensive, rich, flexible, extensible, battle-tested, production-grade.

"A robust parser" says nothing. "The parser accepts every payload the relay emits,
including the zero-length case" says something.

## Structural patterns

**Binary contrast.** "Not a cache. A ledger." State what it is. `It is a ledger.`

**Negative listing.** "Not a queue. Not a buffer. A ring." Same fix.

**Dramatic fragmentation.** "Speed. That is the tradeoff." Write the sentence.

**Self-posed rhetorical question.** "Why does this matter? Because the pool can fail."
Fold it: "The pool can fail, so the row is checked first."

**Anaphora.** Three clauses opening with the same words for rhythm. Keep one.

**Tricolon.** Three parallel items where one or two carry the content. Two beats three.

**Participle summary tail.** ", ensuring correctness", ", allowing flexibility", ",
making the code easier to reason about", ", highlighting the importance of X". These
assert a benefit the sentence did not earn. Cut the tail.

**False range.** "from parsing to settlement", "from A to Z" where the endpoints are
arbitrary and the range means nothing.

**Invented concept label.** "the settlement paradox", "the double-writer problem", "the
N+1 oracle trap". A name is fine when the codebase already uses it. A name coined inside
one comment is a claim to profundity.

**Stakes inflation.** "This fundamentally reshapes how the protocol handles risk." Scale
the claim to what changed.

**Fractal summary.** Say what you are about to say, say it, then summarize what you said.
Say it once.

**Historical analogy stacking.** "Apple did not build Uber. Facebook did not build
Spotify." Never in a code comment.

## Meta-commentary

The text should move, not announce its own structure.

"In this section we'll...", "The rest of this doc explains...", "As we'll see...", "As
mentioned above" (link or repeat the fact), "In conclusion", "To sum up", "In summary",
"Hint:", "Plot twist:", "Spoiler:", "But that's another topic", "X is a feature, not a
bug".

## Vague declaratives

They announce importance without naming the thing.

"The implications are significant", "The reasons are structural", "The stakes are high",
"This is the deepest problem", "There are several considerations here", "This has
important consequences".

Name the implication, the reason, the consequence.

## Vague attribution

"Experts argue", "It is generally accepted that", "Industry practice suggests",
"Observers have noted". In code, the equivalent is "for various reasons" and "for
historical reasons". Name the reason or delete the clause.

## Formatting tells

- Bold-lead bullets: every list item opening with a bolded keyword and a colon.
- Em dashes anywhere.
- Unicode arrows in prose.
- Emoji section headers.
- A "Summary of changes" heading over a list that restates the diff.
- A closing offer: "Let me know if you want me to", "Happy to adjust".
- Signposted conclusion: "Despite these challenges, ...".

## Code-comment specific

**Restating the signature.**
```rust
// BAD
/// Returns the user's collateral.
/// # Arguments
/// * `user` - the user
fn collateral(user: &User) -> u64
```
Delete it. The signature says all of that.

**Narrating control flow.**
```rust
// BAD
// Loop over each market
for market in markets {
```

**Section banners inside a function.** `// --- validation ---`. If the function needs
sections, it needs to be split.

**Changelog comments.** `// Changed in v2 to use u128`. Git holds this.

**Defensive apology.** "This is a bit hacky", "not ideal but", "temporary until we".
Either state the constraint that forces the shape, or delete.

**Ownerless TODO.** `// TODO: revisit`. A TODO needs the condition that makes it
actionable: `// TODO: remove once every market carries a quote_spot_market_index.`

**Plan codenames.** "the S5 rule", "Phase 2", "per the sync log", "as the spec warns",
"deferred to a later phase". A reader has the code, not the plan. Write the reason.

Naming a stable artifact is fine: a crate, a type, a module path, a durable design doc
that explains a whole subsystem. Those are things a reader can open, and they move with
the code.

## Worked examples

Before:
```rust
// Here's the key insight: we need to carefully validate the oracle before using it,
// since a stale oracle could potentially cause issues with the settlement amount —
// ensuring correctness here is critical.
```
After:
```rust
// A stale oracle mis-sizes the settlement amount, so the price is gated before use.
```

Before:
```rust
/// This struct serves as a container that is responsible for holding the
/// various pieces of state that the fill path leverages throughout its
/// execution, allowing for a clean separation of concerns.
```
After:
```rust
/// The maps, market, and clock that every step of the fill path reads.
```

Before (PR body):
```
## Summary
I've added a new flag to the order struct as you requested. This elegantly
solves the issue we discussed — let me know if you'd like any changes!
```
After:
```
Marks an order as a migrated taker remainder. The book uses the flag to refuse
a take while a counterparty crosses the order.
```
