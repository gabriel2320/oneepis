"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createActiveProblem,
  createAllergy,
  createMedication,
  createVitalSign,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageAllergies, canManageMedications, canManageProblems, canRecordVitals } from "@/lib/permissions";
import type { ActiveProblemCreate, AllergyCreate, MedicationCreate, VitalSignCreate } from "@/lib/types";
import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  fieldLabels,
  numberOrNull,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewAllergyPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageAllergies(user);
  const [formState, setFormState] = useState({ substance: "", reaction: "", severity: "unknown" });
  const mutation = useMutation({
    mutationFn: (payload: AllergyCreate) => createAllergy(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/alergias`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="alergias">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/alergias`} label="Alergias" />
        <PageTitle title="Agregar alergia" description="Registro puntual, auditado y reversible." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar alergias." />
        ) : null}
        <ClinicalSectionCard title="Alergia">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                substance: formState.substance,
                reaction: emptyToNull(formState.reaction),
                severity: formState.severity as AllergyCreate["severity"],
                recorded_at: new Date().toISOString(),
              });
            }}
          >
            <Field label="Sustancia">
              <Input
                value={formState.substance}
                onChange={(event) => setFormState({ ...formState, substance: event.target.value })}
              />
            </Field>
            <Field label="Reaccion">
              <Input
                value={formState.reaction}
                onChange={(event) => setFormState({ ...formState, reaction: event.target.value })}
              />
            </Field>
            <Field label="Severidad">
              <select
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={formState.severity}
                onChange={(event) => setFormState({ ...formState, severity: event.target.value })}
              >
                <option value="unknown">Desconocida</option>
                <option value="mild">Leve</option>
                <option value="moderate">Moderada</option>
                <option value="severe">Severa</option>
              </select>
            </Field>
            <Button
              type="submit"
              disabled={mutation.isPending || !formState.substance.trim() || DEMO_MODE || !canWrite}
            >
              {mutation.isPending ? "Guardando..." : "Guardar alergia"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}

export function NewMedicationPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageMedications(user);
  const [formState, setFormState] = useState({ name: "", dose: "", route: "", frequency: "" });
  const mutation = useMutation({
    mutationFn: (payload: MedicationCreate) => createMedication(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/medicacion`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="medicacion">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/medicacion`} label="Medicacion" />
        <PageTitle title="Agregar medicamento" description="Medicacion activa del paciente." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar medicacion." />
        ) : null}
        <ClinicalSectionCard title="Medicamento">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                name: formState.name,
                dose: emptyToNull(formState.dose),
                route: emptyToNull(formState.route),
                frequency: emptyToNull(formState.frequency),
                started_on: new Date().toISOString().slice(0, 10),
              });
            }}
          >
            {(["name", "dose", "route", "frequency"] as const).map((field) => (
              <Field key={field} label={fieldLabels[field]}>
                <Input
                  value={formState[field]}
                  onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                />
              </Field>
            ))}
            <Button type="submit" disabled={mutation.isPending || !formState.name.trim() || DEMO_MODE || !canWrite}>
              {mutation.isPending ? "Guardando..." : "Guardar medicamento"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}

export function NewProblemPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageProblems(user);
  const [formState, setFormState] = useState({
    title: "",
    code_system: "",
    code: "",
    onset_date: "",
    notes: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: ActiveProblemCreate) => createActiveProblem(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/problemas`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="problemas">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/problemas`} label="Problemas" />
        <PageTitle title="Agregar problema activo" description="Problema clinico longitudinal." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar problemas activos." />
        ) : null}
        <ClinicalSectionCard title="Problema">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                title: formState.title,
                code_system: emptyToNull(formState.code_system),
                code: emptyToNull(formState.code),
                onset_date: emptyToNull(formState.onset_date),
                notes: emptyToNull(formState.notes),
              });
            }}
          >
            <Field label="Problema">
              <Input
                value={formState.title}
                onChange={(event) => setFormState({ ...formState, title: event.target.value })}
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Sistema codigo">
                <Input
                  value={formState.code_system}
                  onChange={(event) => setFormState({ ...formState, code_system: event.target.value })}
                />
              </Field>
              <Field label="Codigo">
                <Input
                  value={formState.code}
                  onChange={(event) => setFormState({ ...formState, code: event.target.value })}
                />
              </Field>
            </div>
            <Field label="Inicio">
              <Input
                type="date"
                value={formState.onset_date}
                onChange={(event) => setFormState({ ...formState, onset_date: event.target.value })}
              />
            </Field>
            <Field label="Notas">
              <Textarea
                value={formState.notes}
                onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
              />
            </Field>
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWrite || !formState.title.trim()}>
              {mutation.isPending ? "Guardando..." : "Guardar problema"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}

export function NewVitalSignPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canRecordVitals(user);
  const [formState, setFormState] = useState({
    systolic_bp: "",
    diastolic_bp: "",
    heart_rate_bpm: "",
    oxygen_saturation_pct: "",
    temperature_c: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: VitalSignCreate) => createVitalSign(patientId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["vital-signs", patientId] }),
      ]);
      router.push(`/pacientes/${patientId}/signos-vitales`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="signos-vitales">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/signos-vitales`} label="Signos vitales" />
        <PageTitle title="Registrar signos vitales" description="Control puntual del paciente." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar signos vitales." />
        ) : null}
        <ClinicalSectionCard title="Control">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                measured_at: new Date().toISOString(),
                systolic_bp: numberOrNull(formState.systolic_bp),
                diastolic_bp: numberOrNull(formState.diastolic_bp),
                heart_rate_bpm: numberOrNull(formState.heart_rate_bpm),
                oxygen_saturation_pct: emptyToNull(formState.oxygen_saturation_pct),
                temperature_c: emptyToNull(formState.temperature_c),
              });
            }}
          >
            {(["systolic_bp", "diastolic_bp", "heart_rate_bpm", "oxygen_saturation_pct", "temperature_c"] as const).map(
              (field) => (
                <Field key={field} label={fieldLabels[field]}>
                  <Input
                    inputMode="decimal"
                    value={formState[field]}
                    onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                  />
                </Field>
              ),
            )}
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWrite}>
              {mutation.isPending ? "Guardando..." : "Guardar signos"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
