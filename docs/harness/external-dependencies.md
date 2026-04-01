# External Dependencies Contract

> This document defines the truth boundary for external services and runtime dependencies.

## GPT-SoVITS Is The Real Backend

The real synthesis dependency for this project is GPT-SoVITS.

- The canonical local deployment target is `D:\GPT-SoVITS` when that directory is present.
- The web app and pipeline must treat GPT-SoVITS as the real synthesis backend.
- The backend endpoint used in a job must be recorded in the job data and report.

## Endpoint Truth

- If a job is configured to use a local GPT-SoVITS service, the endpoint must be an actual HTTP endpoint.
- If the backend is unavailable, the job must fail honestly.
- Do not silently rewrite a missing real endpoint into a demo endpoint.
- Do not claim that a job used GPT-SoVITS if it used any surrogate path.

## Allowed Fallbacks

Only these fallbacks are acceptable:

- return a clear failure report,
- skip optional post-processing that is explicitly marked optional,
- keep the job record and error report intact for inspection,
- allow retry after the dependency is restored.

## Forbidden Fallbacks

These are not acceptable unless the user explicitly asks for them in the current task:

- switching to a demo synthesizer and calling the result a real conversion,
- fabricating audio output to satisfy a success check,
- hiding dependency failure behind a success status,
- replacing the real GPT-SoVITS endpoint with a mock, stub, or placeholder and then claiming feature completion,
- returning a playable file when the configured backend was never contacted, unless the file is explicitly labeled as a surrogate artifact.

## Failure Behavior

When GPT-SoVITS is missing, unhealthy, or misconfigured:

- the job must fail,
- the report must include the backend failure reason,
- the output path must not be reported as a real successful audiobook,
- the UI must surface the failure clearly,
- retry should remain possible once the backend is fixed.

## Integration Expectations For `D:\GPT-SoVITS`

If `D:\GPT-SoVITS` exists, the project should assume it may be the source of truth for local synthesis. The integration layer must document:

- how the service is started,
- which port or endpoint it exposes,
- which request/response shape is expected,
- what reference audio format is required,
- how health checks are performed,
- which failures are recoverable,
- which failures terminate the job.

## Surrogate Mode

If a surrogate synthesizer exists for development or offline validation:

- it must be opt-in,
- it must be labeled as surrogate or demo,
- it must never be used to claim product completion,
- it must never replace the real backend in acceptance criteria.

