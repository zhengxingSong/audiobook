# Change Control

> Purpose: force high-risk changes through explicit truth checks before they spread.
> Rule: if a change affects product truth, backend truth, or acceptance truth, update harness docs first or in the same task.

## Changes That Require Harness Updates

A task must update one or more harness docs if it changes:

- what "success" means,
- what backend counts as real,
- what endpoint is the default path,
- what the current phase includes or forbids,
- what corpus or rubric is used for acceptance,
- what temporary bridge is active,
- what files are allowed to be committed, ignored, or treated as artifacts.

## Mandatory Review Questions

Before retaining a change, answer these questions:

1. Does this change alter the truth boundary between `real` and `surrogate`?
2. Does it create or expand a temporary bridge?
3. Does it move logic across architecture layers?
4. Does it make the app more operable without making the product more truthful?
5. Does it require a new acceptance case or a new failure mode in reports?

If any answer is `yes`, update the relevant harness docs.

## Retention Gate

Do not keep a change if:

- it improves convenience but weakens truthfulness,
- it adds a fallback path that is not registered,
- it changes phase scope without updating `current-phase.md`,
- it changes runtime labels without updating `terminology-and-truth-labels.md`,
- it changes acceptance behavior without updating the rubric or corpus.

## Required Closeout Note

Every retained milestone should include:

- what changed,
- whether it is `real` or `surrogate`,
- which harness docs were updated,
- which bridge entries changed,
- whether acceptance status changed or remained blocked.

## Drift Response

If a change is discovered after the fact to violate these rules:

- stop treating it as a valid retained improvement,
- label the mismatch explicitly,
- update docs or code until truth is restored,
- do not paper over the mismatch with softer wording.
