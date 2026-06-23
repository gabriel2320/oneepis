type AiChartStepProps = {
  step: string;
  title: string;
  description: string;
};

export function AiChartStep({ step, title, description }: AiChartStepProps) {
  return (
    <div className="flex items-start gap-3 rounded-md border bg-muted/30 p-3">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground">
        {step}
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
