import { createFileRoute, Link } from "@tanstack/react-router";
import { useSimulation } from "@/hooks/useSimulation";
import { ArrowRight } from "lucide-react";
import { LiveBadge } from "@/components/ui/LiveBadge";

export const Route = createFileRoute("/mobile")({
  head: () => ({
    meta: [
      { title: "TRIAGE Mobile" },
      { name: "description", content: "Read-only mobile view of the TRIAGE simulation." },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
    ],
  }),
  component: MobilePage,
});

function MobilePage() {
  const sim = useSimulation();
  const critical = sim.patients.filter((p) => p.status === "CRITICAL");
  const stable = sim.patients.filter((p) => p.status === "STABLE").length;
  const discharged = sim.patients.filter((p) => p.status === "DISCHARGED").length;
  const deceased = sim.patients.filter((p) => p.status === "DECEASED").length;

  return (
    <div className="mx-auto max-w-[420px] bg-background px-4 py-4 text-text-primary">
      <header className="flex items-center justify-between">
        <div className="font-display text-3xl">TRIAGE</div>
        <LiveBadge />
      </header>

      <div className="mt-4 border-l-4 border-emergency bg-surface p-3" style={{ borderRadius: 4 }}>
        <div className="font-mono text-[10px] uppercase tracking-widest text-emergency">
          MASS CASUALTY EVENT
        </div>
        <div className="mt-1 font-mono text-xs text-text-secondary">
          Episode {sim.episode} · Step {sim.step}
        </div>
      </div>

      <div className="mt-4">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Reward
        </div>
        <div className="font-mono text-4xl text-stable">
          {sim.currentReward.toFixed(1)}
          <span className="ml-2 text-sm text-stable">↑ +37.4 from baseline</span>
        </div>
      </div>

      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Critical Patients ({critical.length})
        </div>
        <div className="mt-2 space-y-1.5">
          {critical.slice(0, 6).map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between border border-border bg-surface px-3 py-2"
              style={{ borderRadius: 4 }}
            >
              <div>
                <div className="font-mono text-[11px] text-text-primary">{p.id}</div>
                <div className="text-[12px] text-text-secondary">{p.condition}</div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emergency" />
                <span className="font-mono text-[10px] text-text-secondary">{p.ward}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <Tile label="STABLE" v={stable} c="var(--stable-green)" />
        <Tile label="DISCHARGED" v={discharged} c="var(--text-muted)" />
        <Tile label="DECEASED" v={deceased} c="var(--emergency-red)" />
      </div>

      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Latest Agent Actions
        </div>
        <div className="mt-2 space-y-1.5">
          {sim.messages.slice(0, 5).map((m) => (
            <div
              key={m.id}
              className="border border-border bg-surface px-3 py-2"
              style={{ borderRadius: 4 }}
            >
              <div className="font-mono text-[10px] text-text-muted">
                {m.from} · {m.type}
              </div>
              <div className="text-[12px] text-text-primary">{m.content}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Resources
        </div>
        <div className="mt-2 space-y-2">
          <Bar label="ICU Beds" used={sim.resources.icuBeds.used} total={sim.resources.icuBeds.total} />
          <Bar label="Ventilators" used={sim.resources.ventilators.used} total={sim.resources.ventilators.total} />
          <Bar label="Blood Supply" used={sim.resources.bloodSupply} total={100} suffix="%" />
          <Bar label="Staff" used={sim.resources.staffOnDuty.used} total={sim.resources.staffOnDuty.total} />
        </div>
      </div>

      <Link
        to="/dashboard"
        className="mt-6 inline-flex w-full items-center justify-center gap-2 bg-primary px-4 py-3 font-mono text-[11px] uppercase tracking-wider text-primary-foreground"
        style={{ borderRadius: 4 }}
      >
        View Full Dashboard <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}

function Tile({ label, v, c }: { label: string; v: number; c: string }) {
  return (
    <div className="border border-border bg-surface p-2 text-center" style={{ borderRadius: 4 }}>
      <div className="font-mono text-[9px] uppercase tracking-wider text-text-muted">{label}</div>
      <div className="mt-0.5 font-mono text-lg" style={{ color: c }}>
        {v}
      </div>
    </div>
  );
}

function Bar({ label, used, total, suffix = "" }: { label: string; used: number; total: number; suffix?: string }) {
  const pct = (used / total) * 100;
  const color = pct > 80 ? "var(--emergency-red)" : pct > 60 ? "var(--warning-amber)" : "var(--stable-green)";
  return (
    <div>
      <div className="flex items-center justify-between font-mono text-[11px]">
        <span className="text-text-secondary">{label}</span>
        <span style={{ color }}>{used}{suffix}/{total}{suffix}</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden bg-surface-2" style={{ borderRadius: 1 }}>
        <div className="h-full" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}
