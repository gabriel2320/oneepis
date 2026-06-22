"use client";

import { Palette } from "lucide-react";
import { useEffect, useState } from "react";

import { TEMPLATE_STORAGE_KEY } from "@/app/providers";
import { cn } from "@/lib/utils";

export type VisualTemplate = "clinical-sober" | "hospital-night" | "ambulatory-warm";

const templates: { value: VisualTemplate; label: string; swatch: string }[] = [
  { value: "clinical-sober", label: "Clinico sobrio", swatch: "bg-teal-700" },
  { value: "hospital-night", label: "Hospital nocturno", swatch: "bg-cyan-500" },
  { value: "ambulatory-warm", label: "Ambulatorio calido", swatch: "bg-emerald-700" },
];

export function TemplateSelector({ compact = false }: { compact?: boolean }) {
  const [template, setTemplate] = useState<VisualTemplate>(() => {
    if (typeof window === "undefined") {
      return "clinical-sober";
    }

    return (window.localStorage.getItem(TEMPLATE_STORAGE_KEY) as VisualTemplate | null) ?? "clinical-sober";
  });

  useEffect(() => {
    document.documentElement.dataset.template = template;
    window.localStorage.setItem(TEMPLATE_STORAGE_KEY, template);
  }, [template]);

  function handleChange(value: VisualTemplate) {
    setTemplate(value);
  }
  const selectedTemplate = templates.find((item) => item.value === template) ?? templates[0];

  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      {!compact ? <Palette className="h-4 w-4" /> : null}
      <span
        aria-hidden="true"
        className={cn("h-3 w-3 rounded-full border border-border", selectedTemplate.swatch)}
      />
      <select
        className="h-9 min-w-0 rounded-md border bg-background px-2 text-sm text-foreground"
        value={template}
        onChange={(event) => handleChange(event.target.value as VisualTemplate)}
      >
        {templates.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export { templates };
