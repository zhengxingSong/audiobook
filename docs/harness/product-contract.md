# Product Contract

> This document defines the truth boundary for the audiobook product.  
> If implementation and this contract conflict, this contract wins.

## Product Goal

The product is a Chinese novel-to-audiobook system that produces a real playable audiobook with:

- distinct narration and character voices,
- visible character/scene/emotion reasoning in reports,
- a browser workflow that can submit, track, inspect, and download jobs,
- a real synthesis backend, not a mock or demo-only path.

## What Counts As Real Success

A build or run may be called successful only if all of the following are true:

- the web app accepts a novel upload or path submission,
- the job runs to a terminal state with a persisted report,
- the pipeline produces a real output audio file,
- the output file can be downloaded and played,
- the report contains fragment-level evidence,
- the report shows character-level grouping and emotion-level evidence,
- narration and character speech are not collapsed into one undifferentiated voice when the source text contains both.

## What Is Not Success

Do not call the product complete, finished, or production-ready if any of these are true:

- the system only renders pages but cannot complete a conversion,
- a demo or fake synthesizer is used instead of the real TTS backend,
- the job returns success without producing a real output file,
- the report contains only generic job metadata without fragment evidence,
- all text is rendered in one narrator voice when the input contains dialogue,
- emotion is detected in code but not reflected in the synthesis path,
- the result depends on manual intervention that is not part of the documented workflow.

## Completion Rules

- A temporary workaround is allowed only if it is explicitly labeled as temporary and the contract still records the gap.
- Any fallback that changes the synthesis backend must be treated as a failure unless the user explicitly approved that fallback for the current task.
- "Web service works" is not equivalent to "product works".
- "Audio file exists" is not equivalent to "product works" unless the file came from the real synthesis path and the semantic report matches the source text.

## Reporting Rules

Every completion summary must state:

- which backend was used,
- whether narration and characters were separated,
- whether emotion was reflected in synthesis,
- whether the output is real or a temporary surrogate,
- which known gaps remain.

## Anti-Drift Rule

If a future implementation increases convenience but weakens truthfulness, keep the truthful version.

