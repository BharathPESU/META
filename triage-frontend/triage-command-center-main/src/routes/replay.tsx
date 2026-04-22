import { createFileRoute } from "@tanstack/react-router";
import { Play, Pause, SkipBack, SkipForward, Rewind, FastForward } from "lucide-react";
import { Navbar } from "@/components/nav/Navbar";
import { useReplay } from "@/hooks/useReplay";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { KeyMoment, MessageType } from "@/lib/types";

export const Route = createFileRoute("/replay")({
  head: () => ({
    meta: [
      { title: "Episode Replay · TRIAGE" },
      { name: "description", content: "Scrub through past TRIAGE episodes step by step." },
      { property: "og:title", content: "TRIAGE Episode Replay" },
      { property: "og:description", content: "Step through stored episodes and inspect the exact moment CMO oversight catches a violation." },
    ],
  }),
  component: ReplayPage,
});

const MOMENT_COLOR: Record<KeyMoment["type"], string> = {
  violation: "var(--emergency-red)",
  oversight_catch: "var(--agent-purple)",
  drug_shortage: "var(--warning-amber)",
  icu_full: "var(--warning-amber)",
  crisis_resolved: "var(--stable-green)",
  patient_death: "var(--emergency-red)",
  drift_event: "var(--clinical-blue)",
};

function ReplayPage() {
  const r = useReplay();
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="mx-auto max-w-[1600px] space-y-3 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border border-border bg-surface p-4" style={{ borderRadius: 8 }}>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
              Episode Replay
            </div>
            <h1 className="font-display mt-1 text-2xl text-text-primary">{r.episode.label}</h1>
          </div>
          <div className="flex items-center gap-2">
            {r.episodes.map((ep) => (
              <button
                key={ep.id}
                onClick={() => r.selectEpisode(ep.id)}
                className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-wider ${ep.id === r.episode.id ? "bg-primary text-primary-foreground" : "border border-border bg-surface text-text-secondary"}`}
                style={{ borderRadius: 4 }}
              >
                EP {ep.episode}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-12 gap-3">
          <div className="col-span-12 lg:col-span-5">
            <ReplayPatientBoard patients={r.patientStateAtStep} step={r.currentStep} />
          </div>
          <div className="col-span-12 lg:col-span-7">
            <ReplayMessageLog messages={r.messagesAtStep} step={r.currentStep} />
          </div>
        </div>

        <Scrubber r={r} />
      </div>
    </div>
  );
}

function ReplayPatientBoard({
  patients,
  step,
}: {
  patients: ReturnType<typeof useReplay>["patientStateAtStep"];
  step: number;
}) {
  return (
    <div className="border border-border bg-surface" style={{ borderRadius: 8 }}>
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Patient State · step {step}
        </div>
        <div className="font-mono text-[10px] text-text-muted">{patients.length} patients</div>
      </div>
      <div className="max-h-[420px] overflow-auto">
        {patients.slice(0, 18).map((p) => (
          <div
            key={p.id}
            className="grid grid-cols-[80px_1fr_120px_50px] items-center gap-3 border-b border-border px-3 py-2 text-xs"
          >
            <div className="font-mono text-[11px] text-text-primary">{p.id}</div>
            <div className="truncate text-text-primary">{p.name} · {p.condition}</div>
            <StatusBadge status={p.status} />
            <div
              className="text-right font-mono text-[11px]"
              style={{
                color:
                  p.triageScore >= 8
                    ? "var(--emergency-red)"
                    : p.triageScore >= 5
                      ? "var(--warning-amber)"
                      : "var(--stable-green)",
              }}
            >
              {p.triageScore}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReplayMessageLog({
  messages,
  step,
}: {
  messages: ReturnType<typeof useReplay>["messagesAtStep"];
  step: number;
}) {
  const typeColor: Record<MessageType, string> = {
    OVERSIGHT: "var(--agent-purple)",
    ALERT: "var(--emergency-red)",
    HANDOFF: "var(--stable-green)",
    ACTION: "var(--clinical-blue)",
    REQUEST: "var(--text-muted)",
  };
  return (
    <div className="border border-border bg-surface" style={{ borderRadius: 8 }}>
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          Message Log · up to step {step}
        </div>
        <div className="font-mono text-[10px] text-text-muted">{messages.length} messages</div>
      </div>
      <div className="max-h-[420px] space-y-2 overflow-auto p-3">
        {messages.length === 0 && (
          <div className="grid h-full place-items-center font-mono text-[11px] text-text-muted">
            Scrub forward to populate the log…
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className="border border-border bg-surface px-3 py-2"
            style={{ borderRadius: 4, borderLeft: `3px solid ${typeColor[m.type]}` }}
          >
            <div className="flex items-center gap-2 font-mono text-[10px]">
              <span style={{ color: typeColor[m.type] }}>{m.type}</span>
              <span className="text-text-primary">{m.from}</span>
              <span className="text-text-muted">→</span>
              <span className="text-text-primary">{m.to}</span>
            </div>
            <div className="mt-1 text-[12px] text-text-primary">{m.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Scrubber({ r }: { r: ReturnType<typeof useReplay> }) {
  return (
    <div className="border border-border bg-surface p-4" style={{ borderRadius: 8 }}>
      <div className="flex items-center gap-2">
        <CtrlBtn onClick={() => r.setStep(0)}>
          <SkipBack className="h-3 w-3" />
        </CtrlBtn>
        <CtrlBtn onClick={() => r.setStep(Math.max(0, r.currentStep - 10))}>
          <Rewind className="h-3 w-3" />
        </CtrlBtn>
        <CtrlBtn onClick={r.togglePlay}>
          {r.isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
        </CtrlBtn>
        <CtrlBtn onClick={() => r.setStep(Math.min(r.episode.totalSteps, r.currentStep + 10))}>
          <FastForward className="h-3 w-3" />
        </CtrlBtn>
        <CtrlBtn onClick={() => r.setStep(r.episode.totalSteps)}>
          <SkipForward className="h-3 w-3" />
        </CtrlBtn>
        <div className="ml-2 flex items-center gap-1">
          {[0.5, 1, 2, 4].map((s) => (
            <button
              key={s}
              onClick={() => r.setSpeed(s)}
              className={`px-2 py-1 font-mono text-[10px] ${r.speed === s ? "bg-primary text-primary-foreground" : "border border-border text-text-secondary"}`}
              style={{ borderRadius: 3 }}
            >
              {s}×
            </button>
          ))}
        </div>
        <div className="ml-auto font-mono text-[12px] text-text-secondary">
          Step {r.currentStep} / {r.episode.totalSteps} · Reward {r.rewardAtStep.toFixed(1)}
        </div>
      </div>

      <div className="relative mt-5 pb-6">
        <input
          type="range"
          min={0}
          max={r.episode.totalSteps}
          value={r.currentStep}
          onChange={(e) => r.setStep(parseInt(e.target.value))}
          className="w-full accent-[var(--clinical-blue)]"
        />
        <div className="relative mt-1 h-6">
          {r.keyMoments.map((m) => {
            const left = (m.step / r.episode.totalSteps) * 100;
            return (
              <button
                key={m.step}
                onClick={() => r.jumpToMoment(m.step)}
                className="group absolute -translate-x-1/2"
                style={{ left: `${left}%` }}
                title={`Step ${m.step}: ${m.description}`}
              >
                <div
                  className="h-3 w-3 rotate-45"
                  style={{ background: MOMENT_COLOR[m.type], border: "1px solid var(--surface)" }}
                />
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-1 sm:grid-cols-2 lg:grid-cols-3">
        {r.keyMoments.map((m) => {
          const isCurrent = Math.abs(m.step - r.currentStep) < 5;
          return (
            <button
              key={m.step}
              onClick={() => r.jumpToMoment(m.step)}
              className={`flex items-start gap-2 border bg-surface px-2.5 py-1.5 text-left transition-colors ${isCurrent ? "border-primary" : "border-border hover:border-primary"}`}
              style={{ borderRadius: 4 }}
            >
              <div
                className="mt-1.5 h-2 w-2 shrink-0 rotate-45"
                style={{ background: MOMENT_COLOR[m.type] }}
              />
              <div>
                <div className="font-mono text-[10px] text-text-muted">Step {m.step}</div>
                <div className="text-[11px] text-text-primary">{m.description}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CtrlBtn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center justify-center border border-border bg-surface px-2 py-1.5 text-text-primary hover:border-primary"
      style={{ borderRadius: 4 }}
    >
      {children}
    </button>
  );
}
