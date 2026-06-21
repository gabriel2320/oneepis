# OneEpis Web

Next.js clinical workspace for OneEpis.

## Commands

From the repository root:

```bash
npm run dev:web
npm run check:web
npm run check:e2e
```

## UI Rules

- Keep screens task-first. This is a clinical tool, not a marketing site.
- Use shadcn-style primitives from `src/components/ui`.
- Keep patient and module screens in `src/components/clinical`.
- Keep printable sheets in `src/components/print`.
- Keep API access in focused clients under `src/lib/api`.
- Use `components/clinical-record` only as legacy code being retired.
