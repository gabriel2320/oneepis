"use client";

import { Palette } from "lucide-react";
import { useEffect, useState } from "react";

import { TEMPLATE_STORAGE_KEY } from "@/app/providers";

export type VisualTemplate = "clinical-sober" | "hospital-night" | "ambulatory-warm";

const templates: { value: VisualTemplate; label: string }[] = [
  { value: "clinical-sober", label: "Clinico sobrio" },
  { value: "hospital-night", label: "Hospital nocturno" },
  { value: "ambulatory-warm", label: "Ambulatorio calido" },
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

  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      {!compact ? <Palette className="h-4 w-4" /> : null}
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
