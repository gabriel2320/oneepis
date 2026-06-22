import type { RuleFindingView } from "./ai-chart-utils";

export type SoapDraftState = {
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

export type HumanReviewConfirmation = {
  human_reviewed: true;
  human_reviewed_at: string;
};

export type RuleFindingGroup = {
  label: string;
  items: RuleFindingView[];
};
