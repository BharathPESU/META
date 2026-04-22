import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PatientStatus } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

const seed = [
  { id: "#PT-0042", cond: "Polytrauma", status: "CRITICAL" as PatientStatus, t: 9 },
  { id: "#PT-0039", cond: "Cardiac Arrest", status: "CRITICAL" as PatientStatus, t: 10 },
  { id: "#PT-0036", cond: "Septic Shock", status: "SERIOUS" as PatientStatus, t: 7 },
  { id: "#PT-0034", cond: "Burns >40%", status: "CRITICAL" as PatientStatus, t: 9 },
  { id: "#PT-0030", cond: "Stroke", status: "SERIOUS" as PatientStatus, t: 6 },
  { id: "#PT-0028", cond: "Internal Bleeding", status: "SERIOUS" as PatientStatus, t: 7 },
  { id: "#PT-0024", cond: "Anaphylaxis", status: "STABLE" as PatientStatus, t: 3 },
  { id: "#PT-0019", cond: "Overdose", status: "STABLE" as PatientStatus, t: 2 },
  { id: "#PT-0014", cond: "Head Trauma", status: "DISCHARGED" as PatientStatus, t: 1 },
  { id: "#PT-0011", cond: "Spinal Injury", status: "DISCHARGED" as PatientStatus, t: 1 },
];

const flow: PatientStatus[] = ["CRITICAL", "SERIOUS", "STABLE", "DISCHARGED"];

export function MiniPatientBoard() {
  const [rows, setRows] = useState(seed);

  useEffect(() => {
    const t = setInterval(() => {
      setRows((prev) => {
        const next = [...prev];
        const idx = Math.floor(Math.random() * next.length);
        const cur = flow.indexOf(next[idx].status);
        const ni = Math.min(flow.length - 1, cur + 1);
        next[idx] = { ...next[idx], status: flow[ni] };
        return next;
      });
    }, 1400);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="border border-border bg-surface" style={{ borderRadius: 8 }}>
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emergency pulse-dot" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-emergency">
            LIVE · MASS CASUALTY
          </span>
        </div>
        <span className="font-mono text-[10px] text-text-muted">EP 7 · STEP 247</span>
      </div>
      <div className="divide-y divide-border">
        <AnimatePresence initial={false}>
          {rows.map((r) => (
            <motion.div
              key={r.id}
              layout
              className="grid grid-cols-12 items-center px-4 py-2.5 text-xs"
            >
              <div className="col-span-3 font-mono text-text-primary">{r.id}</div>
              <div className="col-span-5 text-text-secondary">{r.cond}</div>
              <div className="col-span-2 text-right font-mono text-text-muted">T{r.t}</div>
              <div className="col-span-2 flex justify-end">
                <StatusBadge status={r.status} />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      <div className="border-t border-border bg-surface-2 px-4 py-2 font-mono text-[10px] text-text-muted">
        ER TRIAGE → ICU MGMT · transferring #PT-0042 · GCS 8
      </div>
    </div>
  );
}
