# Running this across a branch

A large branch has hundreds of violations. Doing them one at a time works and is slow. The
pass below is what a real run looks like, including the mistakes that cost the most time.

## Order of operations

1. **Audit first, then plan.** `find-violations.py --summary` over every changed file. The
   distribution is always long-tailed: a handful of files hold a third of the findings, and
   a hundred files hold one each.
2. **Spacing before comments.** `space-blocks.py` is deterministic and needs no judgment. Run
   it over everything, verify the build, and get it out of the way.
3. **Comments in parallel.** One agent per file, or per small group of files. Give each the
   tool command and the rule that its file must reach zero.
4. **Verify once, at the end.** Per-file builds are wasted work when fifty agents are editing
   at once.
5. **Re-run `space-blocks.py` over everything at the end.** It is idempotent, so it is a
   no-op where nothing is wrong, and it repairs the failure in the next section.

## Failure modes, in the order they will bite

**The diff basis is the first thing to get wrong.** `git diff base...HEAD` numbers lines in
*HEAD's* file. Agents read the *working tree*, which already contains uncommitted edits, so
every line number is off by whatever was inserted above it. The effect is not a clean
under-count: it hides real findings and invents phantom ones. Compare the merge-base against
the working tree instead. The tools here do; anything you write yourself must too.

**Tell the agent the cap, do not make it judge.** Printing `-> MAX N LINES` per finding is
the single highest-value thing in this skill. Without it agents overshoot by one or two lines
and leave findings behind, and the rewrite has to be done twice.

**Insist on iterating.** Rewriting shifts line numbers, which pulls new blocks into the
changed-line window. Agents that run the tool once and declare victory leave 20% behind. Say
"re-run until it reports zero" explicitly.

**Agents will not recognise your own earlier edits.** Several will see the blank lines from
the spacing pass, conclude a rogue hook is corrupting their file, and strip them. Tell them up
front: "blank lines from an earlier mechanical pass — leave them alone." The final
`space-blocks.py` re-run repairs any that did it anyway.

**Watch the span measurement on brace languages.** A TypeScript method whose parameter list
contains an inline object type (`opts?: { a: X; b: Y }`) will have those braces mistaken for
its body unless braces are counted only at paren-depth zero. The symptom is a cap of 4 on a
method with a 35-line body, and the damage is a stripped `@param` table. The tool here counts
correctly; check any reimplementation against exactly this case.

**Two findings are not comment problems, and agents will try to fix them anyway.** Say so in
the prompt: `fn X is N lines` is structural, and the declaration-comment count has a false
positive where a comment explains an algorithm step rather than standing in for a name. Left
unsaid, agents either restructure functions you did not want touched or rename locals
cosmetically to get the count down.

**A file marked done is done under the basis it ran with.** Fix the basis mid-run and the
finished files need re-checking. Budget a mop-up wave.

## Writing the agent prompt

Include, every time:

- The tool invocation, verbatim, with the file path.
- "That cap is the hard target."
- "Re-run until it reports zero findings."
- "Do NOT run builds, linters or tests." Verification is central.
- "Do NOT change program logic. Local variable renames are fine, behaviour changes are not."
- What is layout-critical in *this* file: on-chain struct fields, an IDL mirror, an ABI,
  exported type names. Say "comments only" where that is true.
- What must survive in *this* file: hedges, audit citations, mirror references, units.
- "A comment that must exceed its cap keeps an `allow-verbose:` line saying why."
- "Report what you deliberately left over budget and why."

That last line is what makes the run auditable. Agents comply with it, and their reports are
where you find the judgment calls worth reviewing — including the ones you will want to undo.

## Reviewing what came back

Do not re-read every diff. Read the reports, and check three things:

1. **Dropped facts they flagged.** Most are fine. Some are a cross-file coupling or an
   invariant that should go back. One in ten is worth restoring.
2. **Cross-references they kept.** Open the target. A comment pointing at a function that
   does not contain the fact is worse than the comment they deleted.
3. **Hedges.** `git diff | grep -E '^-.*\b(may|can|usually|might)\b'` over the whole pass.
   Every hit should have a matching `+` line that still hedges.

## Model choice

The detection is a script and needs no model. The deletions — a first line restating the
signature, step narration, a test comment duplicating the test name — are pattern matching
and a cheap model does them well.

Spend the expensive model where a *plausible* rewrite is the risk rather than a bad one:
margin, liquidation, oracle validity, and anything a client builds bytes from. Compressing
prose tends to smooth "may fail" into "fails" and to supply a mechanism that makes a sentence
read well but was never stated. That compiles, passes tests, and lies to the next reader.
