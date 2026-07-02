# Contracts

OpenAPI contracts exported from the FastAPI app.

Refresh with:

```bash
npm run export:openapi
npm run generate:openapi-types
```

`openapi.json` is committed so agents and the frontend can inspect API shape
without running the server. `openapi-types.ts` is generated from that contract
and committed too, so TypeScript code can import API schema types in clean
checkouts without a local generation step.
