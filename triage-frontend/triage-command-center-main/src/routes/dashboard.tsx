import { createFileRoute } from "@tanstack/react-router";
import { memo, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip, Legend } from "recharts";
import { Navbar } from "@/components/nav/Navbar";
import { useSimulation } from "@/hooks/useSimulation";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AGENTS } from "@/lib/constants";
import { StrategyMemoryPanel } from "@/components/dashboard/StrategyMemoryPanel";
import { OnboardingOverlay } from "@/components/dashboard/OnboardingOverlay";
import type { AgentMessage, AgentState, MessageType, Patient, Resources } from "@/lib/types";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Live Demo · TRIAGE" },
      { name: "description", content: "Live multi-agent hospital crisis simulation dashboard." },
      { property: "og:title", content: "TRIAGE Live Demo" },
      { property: "og:description", content: "Watch AI agents coordinate a mass casualty event in real time." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const sim = useSimulation();
  return (
    <div className="flex h-screen flex-col bg-background">
      <Navbar />
      <div data-onboarding-target="crisis_header">
        <CrisisHeader
          episode={sim.episode}
          step={sim.step}
          elapsed={sim.elapsed}
          reward={sim.currentReward}
        />
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 px-3 py-3">
        <div className="col-span-3 min-h-0 flex flex-col gap-3" data-onboarding-target="agent_grid">
          <div className="flex-1 min-h-0">
            <AgentStatusGrid agents={sim.agents} />
          </div>
          <StrategyMemoryPanel />
        </div>
        <div className="col-span-6 min-h-0" data-onboarding-target="patient_board">
          <CenterPanel patients={sim.patients} messages={sim.messages} flashed={sim.flashed} />
        </div>
        <div className="col-span-3 grid min-h-0 grid-rows-[1fr_auto] gap-3" data-onboarding-target="reward_score">
          <RewardCurveChart data={sim.metrics} episode={sim.episode} />
          <ResourcePanel r={sim.resources} />
        </div>
      </div>
      <OnboardingOverlay />
    </div>
  );
}

function fmtTime(s: number) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

function CrisisHeader({ episode, step, elapsed, reward }: { episode: number; step: number; elapsed: number; reward: number }) {
  return (
    <div
      className="flex items-center justify-between border-b border-border bg-surface px-6 py-3"
      style={{ borderLeft: "4px solid var(--emergency-red)" }}
    >
      <div className="flex items-center gap-3">
        <span className="h-2.5 w-2.5 rounded-full bg-emergency pulse-dot" />
        <span className="font-mono text-[12px] uppercase tracking-widest text-emergency">
          MASS CASUALTY EVENT — ACTIVE
        </span>
      </div>
      <div className="flex items-center gap-8 font-mono text-[13px]">
        <span className="text-text-secondary">
          Episode <span className="text-text-primary">{episode} / 10</span>
        </span>
        <span className="text-text-secondary">
          Step: <span className="text-text-primary">{step}</span>
        </span>
        <span className="text-text-secondary">{fmtTime(elapsed)}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[11px] uppercase tracking-wider text-text-muted">Reward</span>
        <span className="font-mono text-[22px] text-stable">{reward.toFixed(1)}</span>
      </div>
    </div>
  );
}

const AgentStatusGrid = memo(function AgentStatusGrid({ agents }: { agents: AgentState[] }) {
  const meta = Object.fromEntries(AGENTS.map((a) => [a.name, a]));
  return (
    <div className="flex h-full flex-col border border-border bg-surface" style={{ borderRadius: 8 }}>
      <PanelHeader title="Agent Status" right={`${agents.length} agents`} />
      <div className="grid flex-1 grid-cols-1 gap-2 overflow-auto p-2">
        {agents.map((a) => {
          const m = meta[a.name];
          const c = m?.color ?? "var(--text-muted)";
          const isProc = a.status === "PROCESSING";
          const statusColor =
            a.status === "ACTIVE"
              ? "var(--stable-green)"
              : a.status === "PROCESSING"
                ? "var(--agent-purple)"
                : a.status === "WAITING"
                  ? "var(--text-muted)"
                  : "var(--emergency-red)";
          return (
            <div
              key={a.key}
              className={`border border-border bg-surface p-3 ${isProc ? "thinking-pulse" : ""}`}
              style={{ borderRadius: 6, borderLeft: `3px solid ${c}` }}
            >
              <div className="flex items-center justify-between">
                <div className="font-mono text-[11px] tracking-wider" style={{ color: c }}>
                  {a.name}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: statusColor }} />
                  <span className="font-mono text-[10px]" style={{ color: statusColor }}>
                    {a.status}
                  </span>
                </div>
              </div>
              <div className="mt-1.5 truncate text-[11px] text-text-secondary">
                {a.currentAction}
              </div>
              <div className="mt-2 font-mono text-[10px] text-text-muted">
                msgs sent: {a.messagesSent}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

function CenterPanel({
  patients,
  messages,
  flashed,
}: {
  patients: Patient[];
  messages: AgentMessage[];
  flashed: Set<string>;
}) {
  const [tab, setTab] = useState<"patients" | "feed">("patients");
  return (
    <div className="flex h-full flex-col border border-border bg-surface" style={{ borderRadius: 8 }}>
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex gap-1">
          {(["patients", "feed"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider ${
                tab === t
                  ? "border border-border bg-surface-2 text-text-primary"
                  : "text-text-muted hover:text-text-primary"
              }`}
              style={{ borderRadius: 4 }}
            >
              {t === "patients" ? "Patient Board" : "Message Feed"}
            </button>
          ))}
        </div>
        <div className="font-mono text-[10px] text-text-muted">
          {tab === "patients" ? `${patients.length} active` : `${messages.length} messages`}
        </div>
      </div>
      {tab === "patients" ? (
        <PatientBoard patients={patients} flashed={flashed} />
      ) : (
        <AgentMessageFeed messages={messages} />
      )}
    </div>
  );
}

const PatientBoard = memo(function PatientBoard({ patients, flashed }: { patients: Patient[]; flashed: Set<string> }) {
  const sorted = [...patients].sort((a, b) => b.triageScore - a.triageScore);
  return (
    <div className="flex-1 overflow-auto">
      <div className="grid grid-cols-[90px_1fr_50px_1.4fr_120px_80px_120px_140px] gap-2 border-b border-border bg-surface-2 px-4 py-2 font-mono text-[10px] uppercase tracking-wider text-text-muted">
        <div>ID</div>
        <div>Name</div>
        <div>Age</div>
        <div>Condition</div>
        <div>Status</div>
        <div>Ward</div>
        <div>Triage</div>
        <div>Agent</div>
      </div>
      <AnimatePresence initial={false}>
        {sorted.map((p) => (
          <motion.div
            key={p.id}
            layout
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className={`grid grid-cols-[90px_1fr_50px_1.4fr_120px_80px_120px_140px] items-center gap-2 border-b border-border px-4 py-2 text-xs ${
              flashed.has(p.id) ? "status-flash" : ""
            }`}
          >
            <div className="font-mono text-text-primary">{p.id}</div>
            <div className="text-text-primary">{p.name}</div>
            <div className="font-mono text-text-secondary">{p.age}</div>
            <div className="text-text-secondary">{p.condition}</div>
            <div>
              <StatusBadge status={p.status} />
            </div>
            <div className="font-mono text-[11px] text-text-secondary">{p.ward}</div>
            <div>
              <TriageBar score={p.triageScore} />
            </div>
            <div className="truncate font-mono text-[10px] text-text-muted">{p.assignedAgent}</div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
});

function TriageBar({ score }: { score: number }) {
  const color = score >= 8 ? "var(--emergency-red)" : score >= 5 ? "var(--warning-amber)" : "var(--stable-green)";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-12 overflow-hidden bg-surface-3" style={{ borderRadius: 2 }}>
        <div className="h-full" style={{ width: `${score * 10}%`, background: color }} />
      </div>
      <span className="font-mono text-[10px]" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

const typeColor: Record<MessageType, string> = {
  ACTION: "var(--clinical-blue)",
  ALERT: "var(--emergency-red)",
  OVERSIGHT: "var(--agent-purple)",
  HANDOFF: "var(--stable-green)",
  REQUEST: "var(--text-muted)",
};

const AgentMessageFeed = memo(function AgentMessageFeed({ messages }: { messages: AgentMessage[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: 0 });
  }, [messages.length]);
  return (
    <div ref={ref} className="flex-1 overflow-auto p-2">
      <AnimatePresence initial={false}>
        {messages.map((m) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-2 border border-border bg-surface px-3 py-2"
            style={{ borderRadius: 4, borderLeft: `3px solid ${typeColor[m.type]}` }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="text-text-muted">
                  {m.timestamp.toLocaleTimeString("en-GB", { hour12: false })}
                </span>
                <span style={{ color: typeColor[m.type] }}>{m.type}</span>
                <span className="text-text-primary">{m.from}</span>
                <span className="text-text-muted">→</span>
                <span className="text-text-primary">{m.to}</span>
              </div>
              {m.patientId && (
                <span className="font-mono text-[10px] text-text-muted">{m.patientId}</span>
              )}
            </div>
            <div className="mt-1 text-[12px] text-text-primary">{m.content}</div>
          </motion.div>
        ))}
      </AnimatePresence>
      {messages.length === 0 && (
        <div className="grid h-full place-items-center font-mono text-[11px] text-text-muted">
          waiting for agent traffic…
        </div>
      )}
    </div>
  );
});

function RewardCurveChart({ data, episode }: { data: ReturnType<typeof useSimulation>["metrics"]; episode: number }) {
  return (
    <div className="flex flex-col border border-border bg-surface" style={{ borderRadius: 8 }}>
      <PanelHeader title="Reward Curve" right={`EP ${episode}/10`} />
      <div className="flex-1 p-3" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
            <XAxis dataKey="episode" stroke="var(--text-muted)" tick={{ fontFamily: "DM Mono", fontSize: 10 }} />
            <YAxis domain={[0, 100]} stroke="var(--text-muted)" tick={{ fontFamily: "DM Mono", fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                fontFamily: "DM Mono",
                fontSize: 11,
              }}
            />
            <Legend wrapperStyle={{ fontFamily: "DM Mono", fontSize: 10 }} />
            <Line
              type="monotone"
              dataKey="baselineScore"
              name="Baseline"
              stroke="var(--text-muted)"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="rewardScore"
              name="TRIAGE"
              stroke="var(--clinical-blue)"
              strokeWidth={2}
              dot={{ r: 3, fill: "var(--clinical-blue)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ResourcePanel({ r }: { r: Resources }) {
  const items = [
    { label: "ICU Beds", used: r.icuBeds.used, total: r.icuBeds.total, suffix: "" },
    { label: "Ventilators", used: r.ventilators.used, total: r.ventilators.total, suffix: "" },
    { label: "Blood Supply", used: r.bloodSupply, total: 100, suffix: "%" },
    { label: "Staff On-Duty", used: r.staffOnDuty.used, total: r.staffOnDuty.total, suffix: "" },
  ];
  return (
    <div className="border border-border bg-surface" style={{ borderRadius: 8 }}>
      <PanelHeader title="Resources" right="LIVE" />
      <div className="grid grid-cols-1 gap-2 p-3">
        {items.map((it) => {
          const pct = (it.used / it.total) * 100;
          const color =
            pct > 80 ? "var(--emergency-red)" : pct > 60 ? "var(--warning-amber)" : "var(--stable-green)";
          return (
            <div key={it.label}>
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-text-secondary">{it.label}</span>
                <span style={{ color }}>
                  {it.used}
                  {it.suffix} / {it.total}
                  {it.suffix}
                </span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden bg-surface-3" style={{ borderRadius: 2 }}>
                <div className="h-full transition-all" style={{ width: `${pct}%`, background: color }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PanelHeader({ title, right }: { title: string; right?: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border px-3 py-2">
      <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">{title}</div>
      {right && <div className="font-mono text-[10px] text-text-muted">{right}</div>}
    </div>
  );
}
