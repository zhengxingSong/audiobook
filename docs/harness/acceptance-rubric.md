# Audiobook Acceptance Rubric

> Purpose: define how to judge whether the app is actually ready as an audiobook product.
> Rule: "task completed" means the result passes the rubric below, not merely that a job ran or a WAV file exists.

## Scoring model

Use four verdicts:
- `pass`
- `partial`
- `fail`
- `blocked`

Use these dimensions in every evaluation:
- Narration vs character separation
- Multi-character differentiation
- Emotion rendering
- End-to-end web flow
- Output integrity
- Truthfulness of runtime mode

## 1. Narration vs Character Separation

Pass criteria:
- Pure narration passages are read with a consistent narrator voice.
- Dialogue passages are not flattened into the narrator voice.
- Mixed paragraphs preserve the boundary between narration and speech.

Partial criteria:
- Some distinction exists, but one or more narration-heavy blocks are still read like dialogue, or vice versa.

Fail criteria:
- The entire novel sounds like a single undifferentiated voice.
- Narration and dialogue are not separable in the output.

## 2. Multi-Character Differentiation

Pass criteria:
- At least three distinct characters can be heard as different voices.
- A character keeps a stable voice across repeated appearances.
- The same speaker does not drift to another speaker's voice without a reason.

Partial criteria:
- The system distinguishes only 2 voices, or one character drifts occasionally.

Fail criteria:
- All speaking roles collapse into one voice.
- Speaker changes are not reflected in the audio.

## 3. Emotion Rendering

Pass criteria:
- At least three clearly different emotional states are audible in the output.
- Emotional shifts are aligned with the text, especially in crisis, surprise, anger, and calm sections.
- The change is perceptible to a listener, not only present in JSON metadata.

Partial criteria:
- Emotion metadata exists, but the audible difference is weak or inconsistent.

Fail criteria:
- Every line sounds neutral.
- Emotion is only recorded in reports and not reflected in audio behavior.

## 4. End-to-End Web Flow

Pass criteria:
- Upload a novel through the web app.
- Create a job successfully.
- Observe job state progression.
- Download the result audio from the job page or API.
- Open the report and inspect fragments/characters/emotions.

Partial criteria:
- The job can be created and completed, but one of download/report/details is missing or unstable.

Fail criteria:
- The browser flow breaks before a result can be downloaded.
- The service only works through manual backend calls.

## 5. Output Integrity

Pass criteria:
- The generated file is a valid audio file.
- The output is non-empty and consistent with the requested format.
- The report matches the produced artifact.

Partial criteria:
- The file exists but integrity or report alignment is weak.

Fail criteria:
- A file exists but is not a usable audio artifact.
- The job reports success without a real result file.

## 6. Truthfulness of Runtime Mode

Pass criteria:
- Real product readiness runs use the real GPT-SoVITS path.
- Demo or mock synthesis is clearly labeled and never counted as product acceptance.

Partial criteria:
- Demo mode is used for infrastructure verification only, with explicit labeling.

Fail criteria:
- Demo or mock synthesis is represented as if it were real product capability.

## Acceptance gates

### Infrastructure gate

Required:
- `/health` is green.
- `/api/jobs` accepts a real upload.
- A job can reach `succeeded` or `failed` honestly.

This gate only proves the app is operable.

### Product gate

Required:
- Corpus A passes narration/character distinction.
- Corpus B passes multi-character differentiation.
- Corpus C passes emotion rendering.
- Corpus D passes narration-only handling.
- The run uses the real GPT-SoVITS endpoint, not a demo endpoint.

This gate proves the product claim.

## Suggested decision rule

Treat the app as ready only if all of these are true:
- Product gate passes.
- No blocker exists in output integrity.
- No untruthful fallback is active.
- The web flow can be repeated twice in a row without manual repair.

If a run uses `demo://tone`, mark it `infrastructure-only` and do not use it to close product acceptance.
