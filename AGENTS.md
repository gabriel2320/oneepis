# OneEpis Agent Guide

This repository is designed to be maintained by human developers and AI agents without uncontrolled growth.

## Non-negotiables

- Read `docs/GOVERNANCE.md` before creating features, screens, modules, dependencies, scripts, or docs.
- Keep clinical truth in the backend database model first. The UI and AI modules must not become the source of truth.
- Never commit real patient data, national identifiers, clinical documents, tokens, or production exports.
- Do not add a dependency unless it removes meaningful complexity. Document new dependencies in `docs/GOVERNANCE.md` or an ADR.
- Prefer small modules with clear ownership over broad utility files.
- Keep AI features behind provider interfaces. Ollama is planned, but no clinical diagnosis should be generated without explicit safety review.
- Preserve OpenAPI as the frontend-backend contract.

## Change Workflow

1. Read the nearest README, this file, and `docs/GOVERNANCE.md` before modifying a module.
2. Make the smallest coherent change.
3. Update schemas, OpenAPI export, docs, and tests when behavior changes.
4. Run the checks relevant to the touched surface:
   - Web: `npm --workspace apps/web run typecheck`
   - API: `python -m pytest apps/api/tests`
   - OpenAPI: `python apps/api/scripts/export_openapi.py`
5. Leave unrelated files untouched.

## Code Boundaries

- `apps/web`: Next.js clinical workspace and UI components.
- `apps/api`: FastAPI service, clinical models, validation, audit, and AI provider contracts.
- `packages/contracts`: generated API contracts consumed by clients.
- `infra`: local infrastructure only.
- `docs`: product, architecture, safety, and governance notes.

## Anti-bloat Rules

- Patient/ficha/paper is the center; dashboards, labs, and AI panels are secondary surfaces.
- No new global state library until multiple screens require shared server/client state.
- No AI orchestration framework until a concrete Ollama workflow needs it.
- No feature enters core without a minimal human flow, explicit data ownership, and clear tests.
- No broad "helpers" folders. Name modules after the domain behavior they own.
- No mock patient data that resembles a real person.
