import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Play, Pause, SkipForward, RotateCcw } from "lucide-react";
import { Navbar } from "@/components/nav/Navbar";
import { useSimulation } from "@/hooks/useSimulation";
import type { Patient, PatientStatus, DecisionLogEntry } from "@/lib/types";
import { AGENTS } from "@/lib/constants";

export const Route = createFileRoute("/visualizer")({
  head: () => ({
    meta: [
      { title: "Hospital Visualizer · TRIAGE" },
      { name: "description", content: "Visualize patient flow and AI agent decisions across the simulated hospital." },
      { property: "og:title", content: "TRIAGE Hospital Visualizer" },
      { property: "og:description", content: "Patient flow, agent positions, and decision log for the TRIAGE simulation." },
    ],
  }),
  component: Visualizer,
});

const ROOMS = [
  { id: "ICU", label: "ICU", x: 40, y: 40, w: 260, h: 160 },
  { id: "WARD-A", label: "Ward A", x: 360, y: 40, w: 160, h: 100 },
  { id: "WARD-B", label: "Ward B", x: 540, y: 40, w: 160, h: 100 },
  { id: "WARD-C", label: "Ward C", x: 720, y: 40, w: 160, h: 100 },
  { id: "PHARMACY", label: "Pharmacy", x: 40, y: 240, w: 200, h: 120 },
  { id: "OR", label: "OR Suite", x: 540, y: 180, w: 340, h: 140 },
  { id: "ER", label: "Emergency Dept", x: 280, y: 400, w: 360, h: 140 },
  { id: "ADMIN", label: "Admin / IT", x: 680, y: 400, w: 200, h: 140 },
];

const STATUS_COLOR: Record<PatientStatus, string> = {
  CRITICAL: "#dc2626",
  SERIOUS: "#d97706",
  STABLE: "#059669",
  DISCHARGED: "#6b7280",
  DECEASED: "#000000",
};

function Visualizer() {
  const sim = useSimulation();
  const [crisis, setCrisis] = useState("MASS_CASUALTY");

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <div className="grid flex-1 grid-cols-12 gap-3 px-3 py-3">
        <aside className="col-span-12 lg:col-span-4 xl:col-span-3 flex flex-col gap-3">
          <Controls
            episode={sim.episode}
            setEpisode={sim.setEpisode}
            isRunning={sim.isRunning}
            toggle={sim.toggleSimulation}
            stepForward={sim.stepForward}
            reset={sim.resetSimulation}
            speed={sim.speed}
            setSpeed={sim.setSpeed}
            crisis={crisis}
            setCrisis={setCrisis}
          />
          <Stats sim={sim} />
        </aside>
        <main className="col-span-12 lg:col-span-8 xl:col-span-9 flex flex-col gap-3">
          <FloorPlan patients={sim.patients} />
          <DecisionLog entries={sim.decisions} />
        </main>
      </div>
    </div>
  );
}

function Controls(props: {
  episode: number;
  setEpisode: (n: number) => void;
  isRunning: boolean;
  toggle: () => void;
  stepForward: () => void;
  reset: () => void;
  speed: number;
  setSpeed: (n: number) => void;
  crisis: string;
  setCrisis: (s: string) => void;
}) {
  return (
    <div className="border border-border bg-surface p-4" style={{ borderRadius: 8 }}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
        Playback
      </div>
      <div className="mt-3 flex gap-2">
        <CtrlBtn onClick={props.toggle}>
          {props.isRunning ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          {props.isRunning ? "Pause" : "Play"}
        </CtrlBtn>
        <CtrlBtn onClick={props.stepForward}>
          <SkipForward className="h-3.5 w-3.5" /> Step
        </CtrlBtn>
        <CtrlBtn onClick={props.reset}>
          <RotateCcw className="h-3.5 w-3.5" /> Reset
        </CtrlBtn>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between font-mono text-[10px] text-text-muted">
          <span>EPISODE</span>
          <span className="text-text-primary">{props.episode} / 10</span>
        </div>
        <input
          type="range"
          min={1}
          max={10}
          value={props.episode}
          onChange={(e) => props.setEpisode(parseInt(e.target.value))}
          className="mt-2 w-full accent-[var(--clinical-blue)]"
        />
      </div>

      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Speed
        </div>
        <div className="mt-2 flex gap-1.5">
          {[0.5, 1, 2].map((s) => (
            <button
              key={s}
              onClick={() => props.setSpeed(s)}
              className={`flex-1 py-1.5 font-mono text-[11px] ${
                props.speed === s
                  ? "bg-primary text-primary-foreground"
                  : "border border-border bg-surface text-text-secondary hover:border-primary"
              }`}
              style={{ borderRadius: 4 }}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Crisis Type
        </div>
        <select
          value={props.crisis}
          onChange={(e) => props.setCrisis(e.target.value)}
          className="mt-2 w-full border border-border bg-surface px-2 py-1.5 font-mono text-[11px] text-text-primary"
          style={{ borderRadius: 4 }}
        >
          <option value="MASS_CASUALTY">MASS_CASUALTY</option>
          <option value="OUTBREAK">OUTBREAK</option>
          <option value="EQUIPMENT_FAILURE">EQUIPMENT_FAILURE</option>
          <option value="STAFF_SHORTAGE">STAFF_SHORTAGE</option>
        </select>
      </div>
    </div>
  );
}

function CtrlBtn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex flex-1 items-center justify-center gap-1.5 border border-border bg-surface px-2 py-1.5 font-mono text-[11px] text-text-primary hover:border-primary"
      style={{ borderRadius: 4 }}
    >
      {children}
    </button>
  );
}

function Stats({ sim }: { sim: ReturnType<typeof useSimulation> }) {
  const total = sim.patients.length;
  const survived = sim.patients.filter((p) => p.status !== "DECEASED").length;
  const survivalRate = total ? (survived / total) * 100 : 0;
  const stats = [
    { label: "Total Patients", value: total, mono: true },
    { label: "Survival Rate", value: `${survivalRate.toFixed(1)}%`, big: true },
    { label: "Avg Triage→Treat", value: "4.2 min" },
    { label: "Compliance", value: "94.3%" },
    { label: "Coordination", value: "88.7%" },
    { label: "Schema Drift Events", value: 3 },
  ];
  return (
    <div className="border border-border bg-surface p-4" style={{ borderRadius: 8 }}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
        Statistics
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="border border-border p-2.5" style={{ borderRadius: 4 }}>
            <div className="font-mono text-[9px] uppercase tracking-wider text-text-muted">
              {s.label}
            </div>
            <div
              className={`mt-1 font-mono text-text-primary ${s.big ? "text-2xl text-stable" : "text-sm"}`}
            >
              {s.value}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 border-t border-border pt-3">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Legend
        </div>
        <div className="mt-2 grid grid-cols-2 gap-1.5 text-[11px]">
          {(["CRITICAL", "SERIOUS", "STABLE", "DISCHARGED"] as PatientStatus[]).map((s) => (
            <div key={s} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: STATUS_COLOR[s] }} />
              <span className="font-mono text-text-secondary">{s}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FloorPlan({ patients }: { patients: Patient[] }) {
  // Track previous ward per patient to detect transitions and trigger glow
  const prevWardRef = useRef<Record<string, string>>({});
  const [glowing, setGlowing] = useState<Record<string, number>>({});

  // Stable in-room jitter offset per patient (doesn't change as patient moves)
  const jitterRef = useRef<Record<string, { rx: number; ry: number }>>({});

  const placed = useMemo(() => {
    return patients.slice(0, 40).map((p) => {
      const room = ROOMS.find((r) => r.id === p.ward) ?? ROOMS[6];
      if (!jitterRef.current[p.id]) {
        const seed = (p.id.charCodeAt(3) * 9301 + p.id.charCodeAt(p.id.length - 1) * 49297) % 233280;
        jitterRef.current[p.id] = {
          rx: (seed % 1000) / 1000,
          ry: ((seed * 7) % 1000) / 1000,
        };
      }
      const { rx, ry } = jitterRef.current[p.id];
      const x = room.x + 16 + rx * (room.w - 32);
      const y = room.y + 24 + ry * (room.h - 40);
      return { p, x, y };
    });
  }, [patients]);

  // Detect ward changes → flag glow for ~1.2s
  useEffect(() => {
    const newGlows: Record<string, number> = {};
    let any = false;
    for (const p of patients) {
      const prev = prevWardRef.current[p.id];
      if (prev !== undefined && prev !== p.ward) {
        newGlows[p.id] = Date.now();
        any = true;
      }
      prevWardRef.current[p.id] = p.ward;
    }
    if (any) {
      setGlowing((g) => ({ ...g, ...newGlows }));
      const ids = Object.keys(newGlows);
      const t = setTimeout(() => {
        setGlowing((g) => {
          const next = { ...g };
          for (const id of ids) delete next[id];
          return next;
        });
      }, 1200);
      return () => clearTimeout(t);
    }
  }, [patients]);

  // agents pinned to relevant rooms
  const agentPositions = [
    { name: "ER TRIAGE", room: "ER", color: "var(--emergency-red)" },
    { name: "ICU MGMT", room: "ICU", color: "var(--clinical-blue)" },
    { name: "PHARMACY", room: "PHARMACY", color: "var(--warning-amber)" },
    { name: "OR LEAD", room: "OR", color: "var(--agent-purple)" },
    { name: "IT", room: "ADMIN", color: "#6b7280" },
  ];

  return (
    <div
      className="relative flex-1 border border-border bg-surface p-3"
      style={{ borderRadius: 8, minHeight: 580 }}
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Hospital Floor Plan · Sector 7
        </div>
        <div className="font-mono text-[10px] text-text-muted">
          {placed.length} patients · {agentPositions.length} agents on floor
        </div>
      </div>
      <svg viewBox="0 0 920 560" className="h-full w-full" style={{ minHeight: 520 }}>
        <defs>
          <filter id="patient-glow" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Corridors */}
        <line x1="170" y1="200" x2="170" y2="240" stroke="var(--border-strong)" strokeDasharray="3 3" />
        <line x1="240" y1="300" x2="540" y2="300" stroke="var(--border-strong)" strokeDasharray="3 3" />
        <line x1="460" y1="140" x2="460" y2="400" stroke="var(--border-strong)" strokeDasharray="3 3" />
        <line x1="640" y1="320" x2="640" y2="400" stroke="var(--border-strong)" strokeDasharray="3 3" />

        {/* Rooms */}
        {ROOMS.map((r) => (
          <g key={r.id}>
            <rect
              x={r.x}
              y={r.y}
              width={r.w}
              height={r.h}
              fill="var(--surface-2)"
              stroke="var(--border-strong)"
              strokeWidth={1}
              rx={6}
            />
            <text
              x={r.x + 10}
              y={r.y + 18}
              fill="var(--text-muted)"
              fontFamily="DM Mono"
              fontSize={10}
              style={{ letterSpacing: 1.5, textTransform: "uppercase" }}
            >
              {r.label} · {r.id}
            </text>
          </g>
        ))}

        {/* Patient dots — animate cx/cy via CSS transition for smooth room-to-room movement */}
        {placed.map(({ p, x, y }) => {
          const isGlow = glowing[p.id] !== undefined;
          return (
            <g key={p.id}>
              {isGlow && (
                <circle
                  cx={x}
                  cy={y}
                  r={11}
                  fill={STATUS_COLOR[p.status]}
                  opacity={0.35}
                  style={{
                    transition: "cx 900ms cubic-bezier(0.4,0,0.2,1), cy 900ms cubic-bezier(0.4,0,0.2,1)",
                    filter: "url(#patient-glow)",
                    animation: "triage-pulse 1.2s ease-out",
                  }}
                />
              )}
              <circle
                cx={x}
                cy={y}
                r={4.5}
                fill={STATUS_COLOR[p.status]}
                stroke="var(--surface)"
                strokeWidth={1.5}
                style={{
                  transition:
                    "cx 900ms cubic-bezier(0.4,0,0.2,1), cy 900ms cubic-bezier(0.4,0,0.2,1), fill 300ms ease",
                }}
              >
                <title>
                  {p.id} · {p.condition} · {p.status}
                </title>
              </circle>
            </g>
          );
        })}

        {/* Agent diamonds */}
        {agentPositions.map((a) => {
          const room = ROOMS.find((r) => r.id === a.room)!;
          const cx = room.x + room.w - 22;
          const cy = room.y + room.h - 18;
          return (
            <g key={a.name} transform={`translate(${cx} ${cy}) rotate(45)`}>
              <rect x={-6} y={-6} width={12} height={12} fill={a.color} stroke="var(--surface)" strokeWidth={1.5} />
              <title>{a.name}</title>
            </g>
          );
        })}
      </svg>
      <style>{`
        @keyframes triage-pulse {
          0%   { opacity: 0.55; transform-origin: center; }
          70%  { opacity: 0.25; }
          100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}

function DecisionLog({ entries }: { entries: DecisionLogEntry[] }) {
  const color = (o: DecisionLogEntry["outcome"]) =>
    o === "OPTIMAL"
      ? "var(--stable-green)"
      : o === "SUBOPTIMAL"
        ? "var(--warning-amber)"
        : "var(--emergency-red)";
  return (
    <div className="border border-border bg-surface" style={{ borderRadius: 8, maxHeight: 240 }}>
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Agent Decision Log
        </div>
        <div className="font-mono text-[10px] text-text-muted">{entries.length} decisions</div>
      </div>
      <div className="max-h-[200px] overflow-auto">
        {entries.length === 0 && (
          <div className="p-4 text-center font-mono text-[11px] text-text-muted">
            no decisions logged yet…
          </div>
        )}
        {entries.map((d) => (
          <div
            key={d.id}
            className="grid grid-cols-[110px_140px_1fr_120px_110px] items-center gap-3 border-b border-border px-4 py-2 text-xs"
          >
            <div className="font-mono text-[10px] text-text-muted">
              {d.timestamp.toLocaleTimeString("en-GB", { hour12: false })}
            </div>
            <div className="font-mono text-[11px] text-text-primary">{d.agent}</div>
            <div className="text-text-secondary">{d.action}</div>
            <div className="font-mono text-[11px] text-text-muted">{d.patientId}</div>
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: color(d.outcome) }} />
              <span className="font-mono text-[10px]" style={{ color: color(d.outcome) }}>
                {d.outcome}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// suppress unused
void AGENTS;
void useEffect;
