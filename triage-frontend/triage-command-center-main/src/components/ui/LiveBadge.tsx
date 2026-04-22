import type { WSStatus } from "@/lib/types";
import { useWebSocket } from "@/hooks/useWebSocket";

const LABEL: Record<WSStatus, string> = {
  connecting: "CONNECTING",
  connected: "LIVE",
  fallback: "DEMO MODE",
  disconnected: "OFFLINE",
};

const COLOR: Record<WSStatus, string> = {
  connecting: "var(--warning-amber)",
  connected: "var(--stable-green)",
  fallback: "var(--clinical-blue)",
  disconnected: "var(--text-muted)",
};

export function LiveBadge() {
  // No backend yet → falls into "fallback" within ~6s.
  const ws = useWebSocket({ url: undefined });
  const color = COLOR[ws.status];
  const label = LABEL[ws.status];
  const showLatency = ws.status === "connected" || ws.status === "fallback";
  const latencyColor =
    ws.latencyMs > 500 ? "var(--emergency-red)" : ws.latencyMs > 100 ? "var(--warning-amber)" : color;

  return (
    <div
      className="inline-flex items-center gap-1.5 border border-border bg-surface px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider"
      style={{ borderRadius: 4 }}
      title={ws.status === "fallback" ? "Running with simulated data — no backend connected" : ""}
    >
      <span
        className={ws.status === "connected" ? "pulse-dot h-1.5 w-1.5 rounded-full" : "h-1.5 w-1.5 rounded-full"}
        style={{ background: color }}
      />
      <span style={{ color }}>{label}</span>
      {showLatency && (
        <span style={{ color: latencyColor }}>{ws.latencyMs}ms</span>
      )}
    </div>
  );
}
