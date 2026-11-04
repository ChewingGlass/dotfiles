---
name: review-with-me
description: Review a PR together — runs /code-review in the background with findings held back, quizzes you on the mechanism, callsites, and edge cases while you read the diff yourself, then reveals the findings, reconciles them against your answers, and posts the ones that survive as inline PR comments you approve one at a time. Use for "review this PR with me", "quiz me on PR N", "/review-with-me 371".
---

# Review with me

A PR review is finished when the human understands the change, not when a tool prints findings.
This skill runs the automated review and the human's own read in parallel, tests the human's
understanding before showing any findings, and only then writes comments.

## Arguments

`/review-with-me [target] [--effort=<level>] [--no-post]`

- `target` — PR number, PR URL, branch name, or a path. Empty means the current diff.
- `--effort=<low|medium|high|max>` — passed to `/code-review`. Default `high`.
- `--no-post` — never post to GitHub. Print the final comment set instead.

## Hard rules

1. **No spoilers before the quiz.** From the moment the review agent launches until the quiz is
   graded, do not print findings, a diff summary, a bug list, a risk list, or a "here is what this
   PR does" paragraph. Status lines only. The quiz is worthless if you answer it first.
2. **Write the answer key before you ask.** Every quiz question gets its correct option and its
   `file:line` evidence recorded in the notes file *before* the question is asked. Grading against a
   key written afterwards is rationalization.
3. **One question, one verifiable answer.** A quiz option is correct because the code says so, not
   because it sounds sensible. If you cannot point at a line, cut the question.
4. **The human's findings count.** They are reading the PR too. Anything they surface enters the
   comment set on equal footing with the agent's findings.
5. **Every comment is approved before it is posted.** No batch post without a per-comment pass.

## Phase 0 — Resolve the target

Establish what is being reviewed and whether posting is possible.

```bash
gh pr view <target> --json number,title,headRefName,baseRefName,url,state
gh pr diff <target> --name-only
```

If the target is a branch or path with no PR, set `--no-post` behavior for Phase 8 and say so once,
at the start. Create the notes file at `<scratchpad>/review-with-me-<target>.md` — it holds the
worktree path, the answer key, the held findings, and the comment set, so a context compaction does
not lose them.

Then put the PR head on disk so the human can open it in an editor. Never check the PR out into the
directory they are already working in.

```bash
gh pr checkout <n> --repo <owner>/<repo> --detach 2>/dev/null || true   # only if already isolated
# otherwise, from the repo root:
git fetch origin pull/<n>/head:refs/remotes/origin/pr-<n>
git worktree add --detach <repo-root>/.claude/worktrees/pr-<n>-review refs/remotes/origin/pr-<n>
```

Detach on purpose: a review worktree is read-only, and a detached head cannot push or acquire an
upstream. If a worktree for this PR already exists, reuse it rather than making a second one.
Record the absolute path in the notes file and report it in the Phase 3 hand-off.

## Phase 1 — Launch the review, held back

Spawn one subagent so its findings land in the agent's context, not the terminal:

```
Agent(
  subagent_type: "general-purpose",
  description: "held code review",
  prompt: "Invoke the code-review skill: Skill(skill: 'code-review', args: '<target> <effort>').
           Follow it fully. Do NOT call ReportFindings — the findings must not render in the host
           UI. Return the findings as markdown: one block per finding with severity, file:line,
           a one-sentence claim, and a concrete failure scenario (inputs/state -> wrong result).
           Rank most severe first. Return the empty list if nothing survives verification."
)
```

Tell the user one line: the review is running and its findings are held until the quiz.

## Phase 2 — Build the quiz while they read

Immediately post the hand-off (Phase 3) so the human starts reading, then study the diff yourself:
`gh pr diff`, read the changed files whole, and follow the changed symbols out to their callsites.
You are looking for the questions, not for a summary.

Draft 6–10 questions across three bands:

- **Mechanism and edge cases** — what the changed code does at a boundary, on the failure path, on
  the second call, when the input is zero/empty/max, when two effects race.
- **Callsites and blast radius** — who calls the changed function, which caller now behaves
  differently, and which parallel implementation was *not* updated (the mirror file, the other
  language's port, the cached copy, the test fixture).
- **Findings-derived traps** — one question per significant held finding, built so that the
  intuitive-but-wrong answer is exactly the bug the review found. These are the highest-value
  questions: a wrong answer means the human would have merged the bug.

Question craft:

- Options must be mutually exclusive and all plausible. An option nobody would pick teaches nothing.
- Prefer "what happens when…" over "what does this function do". Behavior, not description.
- Quote the relevant snippet in the option `preview` when the question turns on exact code.
- Never signal the answer through option length, hedging, or ordering.

Every question carries a **reading pointer**: the `path:line` range the human should open to
settle it. The pointer names where the answer lives, never what the answer is — "the invalid-oracle
branch of the spot loop" is a pointer, "the size gate that also catches liabilities" is a spoiler.
Put it on its own line at the end of the question text, as `Look at: path:line-line`, so it is
clickable in the terminal. A question you cannot give a pointer for is a question you cannot grade;
cut it.

Write each question, its correct option, its `file:line` evidence, and its reading pointer to the
notes file now.

While drafting, also assemble the **reading map** for the hand-off: the changed files ranked by how
much of the change they carry, each with the line range that matters and a neutral one-clause label
of what lives there. The map is a table of contents, not a summary — it says where to look, never
what is wrong.

## Phase 3 — Hand off

Post a short block:

```
PR #<n> <title> — <k> files, +<a>/-<d>
Checked out at: <absolute worktree path>   (branch <head>, detached)
Review running in the background. Findings held.

Read in this order:
  1. path/to/core.rs:1165-1414   the new walk
  2. path/to/caller.rs:334-370   the trip instruction
  3. path/to/mirror.ts:2433-2637 the SDK mirror
  ...
Then say "ready" and I will quiz you.
```

Keep each map line to a path, a line range, and a neutral label. No verdicts, no "note that…".

Then wait. If they ask a factual question while reading (where does X live, what is Y), answer it
plainly — that is reading support, not a spoiler. Refuse only the direct asks: "what did you find",
"are there bugs", "what should I look at".

## Phase 4 — Quiz

Ask in rounds of 3–4 questions with `AskUserQuestion`. The tool always offers "Other", so the human
can type a real answer instead of picking one; treat a correct free-text answer as correct even when
it does not match an option.

After each round, grade against the key:

- **Correct** — one line confirming it, with the `file:line`.
- **Wrong or partial** — state the actual behavior, cite the line, and say what the wrong answer
  would imply if it were true. No softening, no "great question".

Every question already carries its `Look at:` pointer, so a wrong answer resolves against open code
rather than against your assertion.

Escalate: if a round is clean, make the next round harder — go to the interaction between two
changes rather than either one alone. If a round exposes a gap, spend the next round in that area
until the model of the code is right. Stop after two rounds if both are clean; the human understands
the change and further quizzing is friction.

Then ask what *they* found. Record it in the notes file before revealing anything.

## Phase 5 — Reveal and reconcile

Now show the held findings, sorted into three groups:

- **You caught this** — the finding, plus the answer or note that showed they had it. Confirms the
  read; needs no discussion.
- **New** — the finding, its failure scenario, and the quiz answer it contradicts if there is one.
- **You found this, the review did not** — their findings, restated as claims about the code.

For each finding state the confidence honestly. A finding the agent marked plausible-but-unverified
is labeled as such; do not launder it into a certainty because it is now on a list.

## Phase 6 — Converge

Discuss. The human refutes what they can. Drop a finding the moment the refutation holds — say
"dropped, you are right that X" and move on, no defense of a dead finding. Keep a finding when the
refutation does not actually address the failure scenario, and say which part is unaddressed.

Verify anything still contested against the code rather than arguing from the diff. The output of
this phase is a final list: each surviving finding with an agreed severity and an agreed fix.

## Phase 7 — Draft comments, one at a time

For each surviving finding, draft the inline comment and show it for approval:

```
[3/5] src/ledger/transfer.rs:412

  The credit can fail after the debit lands. A failed credit leaves the user
  debited and nobody paid. Claim the credit first, then apply the debit.

  [approve / edit / drop]
```

Loop until every comment is approved, edited, or dropped. Apply edits verbatim — an edited comment
is the human's words, not a starting point to re-polish.

Comment style — these are read months later by people who were not here:

- State the fact about the code, then the reason it matters. Then stop.
- No second person, no first person, no reference to this conversation or to the review.
- Active voice, simple tenses, one idea per sentence, under 20 words a sentence.
- A comment that only says "this is wrong" is not finished. Name the failure.
- Respect any repo `CLAUDE.md` rules on comment style; they win over this list.

## Phase 8 — Post

With `--no-post` or no PR, print the final set and stop.

Otherwise post all comments as one review, so the PR gets one notification instead of `n`:

```bash
# payload: {"event":"COMMENT","body":"<optional summary>","comments":[
#   {"path":"...","line":412,"side":"RIGHT","body":"..."}, ...]}
gh api --method POST repos/<owner>/<repo>/pulls/<n>/reviews --input <scratchpad>/review.json
```

GitHub rejects a comment on a line outside the diff. On rejection, retry that one comment against
the nearest changed line in the same hunk, and if that fails too, roll it into a single top-level
comment (`gh pr comment`) that carries the `file:line` in its text. Report which comments landed
inline and which did not.

Close with the PR URL, the count posted, and the count dropped during Phase 6.
