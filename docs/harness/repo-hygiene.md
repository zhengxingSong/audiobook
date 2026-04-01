# Repository Hygiene

> Purpose: prevent artifact pollution, naming drift, and temporary-path contamination.
> Rule: the repo must preserve a clear distinction between source, docs, tests, generated artifacts, and local-only runtime outputs.

## File Classes

### Source Of Truth

These are intended to be versioned and reviewed:

- `src/**`
- `tests/**`
- `docs/**`
- stable config files

### Generated Local Artifacts

These are runtime outputs and must not be used as source of truth:

- `output/**`
- `.tmp-test/**`
- local downloaded WAV files
- job reports generated from ad hoc manual runs
- temporary synthesized fragments

Generated local artifacts must not be cited as permanent evidence unless copied into a deliberate docs or fixtures path.

## Commit Discipline

- Do not commit accidental runtime outputs.
- Do not commit one-off debug files without a documented purpose.
- Do not let temporary filenames become part of the public workflow.
- Keep development-only assets clearly separated from acceptance fixtures.

## Naming Rules

- Use `real`, `surrogate`, `infrastructure-only`, and `product-acceptance` exactly as defined in the terminology doc.
- Name development bridges explicitly instead of using vague names like `new_flow`, `temp_fix`, or `final2`.
- Put acceptance fixtures under a stable path if they become permanent.

## Default Path Hygiene

- Defaults exposed in the web UI or API must be reviewed for truthfulness.
- A surrogate default must be labeled as development-only and recorded in the bridge register.
- Do not expose a development default as if it were the normal product path.

## Report Hygiene

- Reports must describe what actually happened, not what the system hoped to do.
- If a run used a surrogate backend, the report must say so.
- If a run did not contact the real backend, the report must not imply otherwise.

## Documentation Sync Rule

When a path, default, artifact format, or runtime label changes:

- update the relevant harness docs,
- update tests if the meaning changed,
- remove stale wording in templates, UI text, and summaries.
