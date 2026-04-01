# Harness Documentation Index

> Purpose: keep the project aligned as implementation grows.
> Rule: these files define truth, scope, and anti-drift controls for both humans and agents.

## Reading Order

Read these documents in this order when starting work:

1. `product-contract.md`
2. `external-dependencies.md`
3. `current-phase.md`
4. `architecture-boundaries.md`
5. `agent-harness-rules.md`
6. `acceptance-corpus.md`
7. `acceptance-rubric.md`
8. `terminology-and-truth-labels.md`
9. `temporary-bridges-register.md`
10. `change-control.md`
11. `repo-hygiene.md`
12. `traceability-matrix.md`

## Precedence

If two documents appear to conflict, use this order:

1. `product-contract.md`
2. `external-dependencies.md`
3. `current-phase.md`
4. `architecture-boundaries.md`
5. `acceptance-rubric.md`
6. `agent-harness-rules.md`
7. all remaining harness docs

## What These Docs Prevent

This folder exists to prevent four common forms of project drift:

- truth drift: calling a demo or surrogate result "product complete"
- scope drift: working on attractive side features before the current phase is complete
- boundary drift: pushing business logic into the wrong layer
- hygiene drift: allowing temporary outputs, fallback paths, and one-off scripts to become permanent contamination

## Maintenance Rule

If implementation changes one of the following, the matching harness document must be updated in the same task:

- what counts as success
- what backend is considered real
- what the current phase allows
- where layer boundaries are drawn
- what corpus or rubric is used for acceptance
- what temporary bridge is active
- what files are allowed to be committed or ignored

## Definition Of Done For Documentation

A harness update is complete only when:

- the relevant markdown file exists in this folder,
- the rule is written in unambiguous language,
- any temporary bridge is recorded with removal conditions,
- related code and tests use the same terminology,
- completion summaries can cite the rule directly.
