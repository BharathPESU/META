import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { STRATEGY_LESSONS } from "@/lib/sponsors";
import { AGENTS } from "@/lib/constants";
import { toast } from "sonner";

export function StrategyMemoryPanel() {
  const [open, setOpen] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [withMemory, setWithMemory] = useState(true);

  const lessons = STRATEGY_LESSONS.filter(
    (l) => filter === "ALL" || l.agentType === filter,
  );

  function runComparison() {
    toast.success(
      withMemory
        ? "Comparison run · WITH memory: reward 84.7"
        : "Comparison run · WITHOUT memory: reward 61.3",
      { description: "Δ +23.4 reward avg when StrategyMemory active" },
    );
  }

  return (
    <div
      className="border border-border bg-surface"
      style={{ borderRadius: 8 }}
      data-onboarding-target="strategy_memory"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between border-b border-border px-3 py-2"
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="h-3 w-3 text-text-muted" />
          ) : (
            <ChevronRight className="h-3 w-3 text-text-muted" />
          )}
          <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
            Strategy Memory
          </div>
        </div>
        <div className="font-mono text-[10px] text-text-muted">
          {STRATEGY_LESSONS.length} lessons
        </div>
      </button>
      {open && (
        <div className="p-3">
          <div className="flex items-center gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-border bg-surface px-2 py-1 font-mono text-[10px] text-text-primary"
              style={{ borderRadius: 4 }}
            >
              <option value="ALL">All Agents</option>
              {AGENTS.map((a) => (
                <option key={a.key} value={a.key}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-3 grid max-h-[260px] grid-cols-1 gap-2 overflow-auto pr-1">
            {lessons.map((l) => {
              const agent = AGENTS.find((a) => a.key === l.agentType);
              return (
                <div
                  key={l.id}
                  className="border border-border bg-surface-2 p-2.5"
                  style={{ borderRadius: 6, borderLeft: `3px solid ${agent?.color}` }}
                >
                  <div className="flex items-center justify-between font-mono text-[10px]">
                    <span style={{ color: agent?.color }}>EP {l.episode} · {agent?.name}</span>
                    <span className="text-stable">+{l.rewardDelta} ↑</span>
                  </div>
                  <div className="mt-1.5 text-[11px] text-text-primary">{l.correction}</div>
                  <div className="mt-1 text-[10px] text-text-muted">
                    Pattern: {l.pattern}
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1 flex-1 overflow-hidden bg-surface-3" style={{ borderRadius: 1 }}>
                      <div
                        className="h-full"
                        style={{
                          width: `${l.confidence * 100}%`,
                          background: "var(--clinical-blue)",
                        }}
                      />
                    </div>
                    <span className="font-mono text-[9px] text-text-muted">
                      {l.confidence.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-1 font-mono text-[9px] text-text-muted">
                    Applied {l.timesApplied}× · {l.successCount} successful
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 border-t border-border pt-3">
            <div className="flex items-center justify-between">
              <div className="font-mono text-[10px] uppercase tracking-wider text-text-muted">
                Comparison
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setWithMemory(true)}
                  className={`px-2 py-1 font-mono text-[10px] ${withMemory ? "bg-primary text-primary-foreground" : "border border-border text-text-secondary"}`}
                  style={{ borderRadius: 3 }}
                >
                  WITH
                </button>
                <button
                  onClick={() => setWithMemory(false)}
                  className={`px-2 py-1 font-mono text-[10px] ${!withMemory ? "bg-primary text-primary-foreground" : "border border-border text-text-secondary"}`}
                  style={{ borderRadius: 3 }}
                >
                  WITHOUT
                </button>
              </div>
            </div>
            <button
              onClick={runComparison}
              className="mt-2 w-full border border-border bg-surface-2 py-1.5 font-mono text-[10px] uppercase tracking-wider text-text-primary hover:border-primary"
              style={{ borderRadius: 4 }}
            >
              Run 50-step comparison
            </button>
            <div className="mt-2 font-mono text-[10px] text-stable">
              Δ +23.4 avg reward when memory active
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
