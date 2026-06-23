import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const openApi = JSON.parse(
  readFileSync(path.join(repoRoot, "packages/contracts/openapi.json"), "utf8"),
);
const tsContracts = [
  "apps/web/src/lib/type-contracts/clinical-record.ts",
  "apps/web/src/lib/type-contracts/lab.ts",
]
  .map((contractPath) => readFileSync(path.join(repoRoot, contractPath), "utf8"))
  .join("\n");

const schemaNames = [
  "AssistantTimelineItem",
  "AssistantTimelineResponse",
  "AssistantSearchResult",
  "AssistantSearchResponse",
  "AssistantChartRequest",
  "AssistantChartPoint",
  "AssistantChartSeries",
  "AssistantChartResponse",
  "AssistantCorrelationRequest",
  "AssistantCorrelationEvidence",
  "AssistantCorrelationResult",
  "AssistantCorrelationResponse",
  "LabPanelCreate",
  "LabPanelRead",
  "LabPanelUpdate",
  "LabResultCreate",
  "LabResultRead",
  "LabResultUpdate",
];

const endpointContracts = [
  {
    method: "get",
    path: "/api/v1/patients/{patient_id}/assistant/timeline",
    response: "AssistantTimelineResponse",
  },
  {
    method: "get",
    path: "/api/v1/patients/{patient_id}/assistant/search",
    response: "AssistantSearchResponse",
  },
  {
    method: "post",
    path: "/api/v1/patients/{patient_id}/assistant/chart",
    request: "AssistantChartRequest",
    response: "AssistantChartResponse",
  },
  {
    method: "post",
    path: "/api/v1/patients/{patient_id}/assistant/correlate",
    request: "AssistantCorrelationRequest",
    response: "AssistantCorrelationResponse",
  },
  {
    method: "get",
    path: "/api/v1/patients/{patient_id}/lab-panels",
    responseList: "LabPanelRead",
  },
  {
    method: "post",
    path: "/api/v1/patients/{patient_id}/lab-panels",
    request: "LabPanelCreate",
    response: "LabPanelRead",
    responseStatus: "201",
  },
  {
    method: "get",
    path: "/api/v1/patients/{patient_id}/lab-panels/{panel_id}",
    response: "LabPanelRead",
  },
  {
    method: "patch",
    path: "/api/v1/patients/{patient_id}/lab-panels/{panel_id}",
    request: "LabPanelUpdate",
    response: "LabPanelRead",
  },
  {
    method: "get",
    path: "/api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}",
    response: "LabResultRead",
  },
  {
    method: "patch",
    path: "/api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}",
    request: "LabResultUpdate",
    response: "LabResultRead",
  },
];

const errors = [];

for (const schemaName of schemaNames) {
  const openApiFields = sorted(Object.keys(schema(schemaName).properties ?? {}));
  const tsFields = sorted(typeFields(schemaName));
  if (openApiFields.join("|") !== tsFields.join("|")) {
    errors.push(
      `${schemaName} fields drifted. OpenAPI=[${openApiFields.join(", ")}] TS=[${tsFields.join(", ")}]`,
    );
  }
}

assertNamedUnion(
  "AssistantTimelineItemType",
  schema("AssistantTimelineItem").properties.item_type.enum,
);
assertNamedUnion(
  "AssistantCorrelationPreset",
  schema("AssistantCorrelationResult").properties.preset.enum,
);
assertFieldUnion(
  "AssistantChartPoint",
  "source_type",
  schema("AssistantChartPoint").properties.source_type.enum,
);
assertFieldUnion(
  "AssistantCorrelationEvidence",
  "source_type",
  schema("AssistantCorrelationEvidence").properties.source_type.enum,
);
assertNamedUnion("LabResultFlag", schema("LabResultFlag").enum);

for (const contract of endpointContracts) {
  const operation = openApi.paths?.[contract.path]?.[contract.method];
  if (!operation) {
    errors.push(`Missing Assistant Read endpoint ${contract.method.toUpperCase()} ${contract.path}.`);
    continue;
  }
  if (contract.request) {
    const requestRef = operation.requestBody?.content?.["application/json"]?.schema?.$ref;
    assertRef(
      requestRef,
      contract.request,
      `${contract.method.toUpperCase()} ${contract.path} request`,
    );
  }
  const responseStatus = contract.responseStatus ?? "200";
  const responseSchema =
    operation.responses?.[responseStatus]?.content?.["application/json"]?.schema;
  if (contract.responseList) {
    assertListRef(
      responseSchema,
      contract.responseList,
      `${contract.method.toUpperCase()} ${contract.path} response`,
    );
  } else {
    assertRef(
      responseSchema?.$ref,
      contract.response,
      `${contract.method.toUpperCase()} ${contract.path} response`,
    );
  }
}

if (errors.length > 0) {
  console.error("Assistant Read contract drift detected:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Assistant Read contract guard passed: ${schemaNames.length} schemas checked.`);

function schema(name) {
  const match = openApi.components?.schemas?.[name];
  if (!match) {
    errors.push(`Missing OpenAPI schema ${name}.`);
    return { properties: {} };
  }
  return match;
}

function typeFields(name) {
  const body = objectTypeBody(name);
  return [...body.matchAll(/^\s*([A-Za-z_][A-Za-z0-9_]*)(?:\??):/gm)].map(
    (match) => match[1],
  );
}

function objectTypeBody(name) {
  const pattern = new RegExp(`export type ${name} = \\{([\\s\\S]*?)\\n\\};`, "m");
  const match = tsContracts.match(pattern);
  if (!match) {
    errors.push(`Missing TS object type ${name}.`);
    return "";
  }
  return match[1];
}

function namedUnionValues(name) {
  const pattern = new RegExp(`export type ${name} =([\\s\\S]*?);`, "m");
  const match = tsContracts.match(pattern);
  if (!match) {
    errors.push(`Missing TS union type ${name}.`);
    return [];
  }
  return quotedValues(match[1]);
}

function fieldUnionValues(typeName, fieldName) {
  const body = objectTypeBody(typeName);
  const pattern = new RegExp(`^\\s*${fieldName}\\??:\\s*([^;]+);`, "m");
  const match = body.match(pattern);
  if (!match) {
    errors.push(`Missing TS field ${typeName}.${fieldName}.`);
    return [];
  }
  return quotedValues(match[1]);
}

function assertNamedUnion(name, expectedValues) {
  assertValues(name, expectedValues, namedUnionValues(name));
}

function assertFieldUnion(typeName, fieldName, expectedValues) {
  assertValues(`${typeName}.${fieldName}`, expectedValues, fieldUnionValues(typeName, fieldName));
}

function assertValues(label, expectedValues = [], actualValues = []) {
  const expected = sorted(expectedValues);
  const actual = sorted(actualValues);
  if (expected.join("|") !== actual.join("|")) {
    errors.push(`${label} enum drifted. OpenAPI=[${expected.join(", ")}] TS=[${actual.join(", ")}]`);
  }
}

function assertRef(ref, expectedSchema, label) {
  const expectedRef = `#/components/schemas/${expectedSchema}`;
  if (ref !== expectedRef) {
    errors.push(`${label} expected ${expectedRef}, received ${ref ?? "missing ref"}.`);
  }
}

function assertListRef(schema, expectedSchema, label) {
  const ref = schema?.items?.$ref;
  assertRef(ref, expectedSchema, label);
}

function quotedValues(text) {
  return [...text.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
}

function sorted(values) {
  return [...values].sort((left, right) => left.localeCompare(right));
}
