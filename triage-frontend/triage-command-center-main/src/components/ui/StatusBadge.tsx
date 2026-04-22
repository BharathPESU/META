import type { PatientStatus } from "@/lib/types";

const map: Record<PatientStatus, { label: string; color: string }> = {
  CRITICAL: { label: "CRITICAL", color: "var(--emergency-red)" },
  SERIOUS: { label: "SERIOUS", color: "var(--warning-amber)" },
  STABLE: { label: "STABLE", color: "var(--stable-green)" },
  DISCHARGED: { label: "DISCHARGED", color: "var(--discharged-gray)" },
  DECEASED: { label: "DECEASED", color: "#000000" },
};

export function StatusBadge({ status }: { status: PatientStatus }) {
  const { label, color } = map[status];
  return (
    <span className="inline-flex items-center gap-2 font-mono text-[11px] tracking-wide">
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span style={{ color }}>{label}</span>
    </span>
  );
}
