# Temporary Bridges Register

> Purpose: make temporary compromises visible and finite.
> Rule: no temporary bridge may exist in code unless it is listed here.

## Required Fields

Every bridge entry must contain:

- bridge name
- status
- scope
- reason
- allowed use
- forbidden use
- removal condition
- current owner or next action

Statuses:

- `active`
- `planned-removal`
- `removed`

## Active Bridges

### Bridge: `demo://tone`

- Status: `active`
- Scope: local infrastructure validation only
- Reason:
  - allows the web app, job system, report path, and audio export path to be exercised without a live GPT-SoVITS service
- Allowed use:
  - local smoke testing
  - infrastructure-only web validation
  - artifact handling checks
  - UI and report flow debugging
- Forbidden use:
  - product acceptance
  - release readiness claims
  - any statement that GPT-SoVITS integration is complete
  - any evidence for narration/character/emotion quality
- Removal condition:
  - the default end-to-end flow uses the real GPT-SoVITS backend successfully
  - acceptance corpus runs pass with the real backend
  - demo mode is no longer the default path for job creation
- Current owner or next action:
  - replace default usage with explicit opt-in development mode
  - integrate `D:\GPT-SoVITS` and wire real backend health checks

## Planned Bridge Closures

### Bridge: default job creation uses surrogate endpoint

- Status: `planned-removal`
- Scope: current Web job form and API defaults
- Reason:
  - kept the app operable while real backend integration was missing
- Removal condition:
  - `POST /api/jobs` defaults to real backend configuration or fails clearly when real backend config is absent
- Next action:
  - remove surrogate default and move it behind an explicit dev-only flag

## Registration Rules

- Bridges must be registered before they are merged or presented as retained work.
- If a bridge changes scope, update this file in the same task.
- When a bridge is removed, keep the entry and mark it `removed` for historical traceability.
- Unregistered bridge behavior must be treated as drift and corrected before continuing.
