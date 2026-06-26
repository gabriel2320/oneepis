import { readFileSync, writeFileSync } from "node:fs";
import { readScreenRegistry, renderRouteTable, screenTreePath } from "./screen-registry.mjs";

const startMarker = "<!-- screen-routes:start -->";
const endMarker = "<!-- screen-routes:end -->";
const checkOnly = process.argv.includes("--check");

const current = readFileSync(screenTreePath, "utf8");
const generatedBlock = [
  startMarker,
  "",
  "<!-- Esta tabla se genera desde apps/web/src/lib/screen-capabilities.registry.json. -->",
  "<!-- No editar manualmente: usar npm run generate:screens. -->",
  "",
  renderRouteTable(readScreenRegistry()),
  "",
  endMarker,
].join("\n");

const next = replaceGeneratedBlock(current, generatedBlock);

if (checkOnly) {
  if (next !== current) {
    console.error("SCREEN_TREE route table is out of date. Run npm run generate:screens.");
    process.exit(1);
  }
  console.log("Generated screen route table is up to date.");
} else {
  writeFileSync(screenTreePath, next);
  console.log("Updated docs/SCREEN_TREE.md route table from screen registry.");
}

function replaceGeneratedBlock(markdown, block) {
  const start = markdown.indexOf(startMarker);
  const end = markdown.indexOf(endMarker);
  if (start !== -1 && end !== -1 && end > start) {
    return `${markdown.slice(0, start)}${block}${markdown.slice(end + endMarker.length)}`;
  }

  const heading = "## Rutas reales y estado";
  const nextHeading = "\n## Superficies futuras del mapa maestro";
  const headingIndex = markdown.indexOf(heading);
  const nextHeadingIndex = markdown.indexOf(nextHeading);
  if (headingIndex === -1 || nextHeadingIndex === -1 || nextHeadingIndex <= headingIndex) {
    throw new Error("No se pudo ubicar la seccion de rutas reales en docs/SCREEN_TREE.md.");
  }

  const before = markdown.slice(0, headingIndex + heading.length);
  const after = markdown.slice(nextHeadingIndex);
  return `${before}\n\n${block}\n${after}`;
}
