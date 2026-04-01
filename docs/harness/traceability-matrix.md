# Traceability Matrix

> Purpose: connect product claims to implementation and evaluation.
> Rule: no major claim should exist without a matching implementation path and acceptance path.

## Matrix

| Product claim | Truth source | Primary implementation area | Verification source | Current state |
|---|---|---|---|---|
| Web app can submit and track jobs | `product-contract.md`, `current-phase.md` | `src/audiobook/web/app.py`, `src/audiobook/services/jobs.py` | web API tests, manual browser flow | partial |
| Success means real output audio exists | `product-contract.md` | `src/audiobook/processors/pipeline.py`, `src/audiobook/services/conversion.py` | integration tests, result download checks | partial |
| Real backend is GPT-SoVITS | `external-dependencies.md` | synthesis integration layer | real backend health checks, real endpoint run | blocked |
| Narration and characters are distinct | `product-contract.md`, `acceptance-rubric.md` | parser, character engine, pipeline, synthesis path | Corpus A and B | fail in latest surrogate run |
| Emotion is audible, not metadata-only | `product-contract.md`, `acceptance-rubric.md` | character engine, synthesis engine, prompt/control path | Corpus C | fail in latest surrogate run |
| Narration-only prose is handled honestly | `acceptance-rubric.md` | parser, pipeline | Corpus D | unverified against real backend |
| Temporary surrogate paths are controlled | `temporary-bridges-register.md`, `agent-harness-rules.md` | web defaults, synthesis path, test labels | doc review, config review | partial |

## How To Use This Matrix

- Before making a product claim, locate the matching row.
- If a row has no implementation area, the claim is still design-only.
- If a row has implementation but no verification source, the claim is not yet acceptable.
- If current state is `blocked`, do not soften the claim; fix the blocker or report it.

## Update Triggers

Update this matrix when:

- a new product claim is introduced,
- a bridge is added or removed,
- an acceptance gate changes,
- an implementation area moves across layers,
- a previously blocked claim becomes verifiable.
