# Architecture Boundaries

## Layer Responsibilities

### Web Layer
- Owns HTTP, HTML, form handling, and static assets.
- Must not implement conversion logic inline.
- Must not parse novels, synthesize audio, or choose voices directly.

### Service Layer
- Owns job creation, orchestration, retries, cancellation, and persistence.
- Translates web requests into pipeline work.
- Owns user-facing status and report shaping.

### Pipeline Layer
- Owns novel parsing, character detection, voice matching, synthesis preparation, and export.
- Must stay independent from page rendering and request parsing.
- Must report failure honestly when export is incomplete.

### Storage Layer
- Owns persisted job metadata, voice metadata, cache, and result artifacts.
- Must not contain business rules for character or emotion logic.

### Engine Layer
- Owns parsing, recognition, matching, synthesis, and optional scene analysis.
- Must expose reusable primitives rather than app-specific workflows.

## Boundary Rules
- Web may call services only.
- Services may call pipeline and storage only.
- Pipeline may call engines and storage only.
- Engines may depend on models and utility code only.
- No layer may silently replace a missing real dependency with an unannounced fake path.

## Change Rule
- If a change crosses a layer boundary, move the responsibility into the correct layer instead of duplicating logic.

