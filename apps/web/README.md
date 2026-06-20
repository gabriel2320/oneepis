# OneEpis Web

Next.js clinical workspace for OneEpis.

## Commands

```bash
npm --workspace apps/web run dev
npm --workspace apps/web run typecheck
npm --workspace apps/web run build
```

## UI Rules

- Keep screens task-first. This is a clinical tool, not a marketing site.
- Use shadcn-style primitives from `src/components/ui`.
- Keep clinical modules in `src/components/clinical-record`.
- Keep API access in `src/lib/api.ts`.
