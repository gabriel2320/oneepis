import type { RuleFindingView } from "./ai-chart-utils";

export type SoapDraftState = {
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

export type RuleFindingGroup = {
  label: string;
  items: RuleFindingView[];
};
