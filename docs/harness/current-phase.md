# Current Phase

## Phase Name
Web service validation and real TTS integration.

## What This Phase Must Deliver
- A browser-accessible app that can submit conversion jobs.
- A backend that executes jobs through the real audiobook pipeline.
- A truthful result path: success only when a real audio file exists.
- Evidence for narration, character separation, and emotion handling in job reports.

## In Scope
- FastAPI web routes and HTML pages.
- Job creation, status polling, report retrieval, and result download.
- Voice library CRUD.
- Pipeline execution, progress tracking, and failure reporting.
- Real GPT-SoVITS integration or a clearly declared failure when it is unavailable.

## Non-Goals
- Do not add platform-wide features that do not help the current phase finish.
- Do not treat a demo audio generator as production TTS.
- Do not add scene music, mixing, multi-tenant auth, billing, or desktop packaging here.
- Do not expand the UI beyond what is needed to operate and verify the conversion flow.

## Exit Criteria
- A user can upload a novel, start a job, see progress, and download a result.
- The report shows what happened to narration, characters, and emotion.
- Tests prove the app is honest about success and failure.
- Any temporary fallback path is explicitly labeled and cannot be mistaken for completion.

