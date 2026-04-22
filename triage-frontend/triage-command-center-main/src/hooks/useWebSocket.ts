import { useCallback, useEffect, useRef, useState } from "react";
import type { WSStatus } from "@/lib/types";
import type { BackendStateUpdate } from "@/lib/api";
import { ENDPOINTS } from "@/lib/api";

// ── Public interface ───────────────────────────────────────────────────────────

export interface WebSocketState {
  status: WSStatus;
  latencyMs: number;
  reconnectAttempt: number;
  lastEventAt: Date | null;
  isMockMode: boolean;
  /** Latest state-update pushed from the backend (null when not connected). */
  backendState: BackendStateUpdate | null;
}

interface Options {
  /** Override WebSocket URL; defaults to ENDPOINTS.ws from api.ts */
  url?: string;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  /** Whether to silently fall back to mock mode after max failed attempts. */
  fallbackToMock?: boolean;
  /** Callback fired each time a `state_update` message arrives. */
  onStateUpdate?: (state: BackendStateUpdate) => void;
}

// ── Hook ───────────────────────────────────────────────────────────────────────

export function useWebSocket({
  url = ENDPOINTS.ws,
  reconnectDelay = 2500,
  maxReconnectAttempts = 4,
  fallbackToMock = true,
  onStateUpdate,
}: Options = {}): WebSocketState & {
  sendCommand: (command: string, params?: Record<string, unknown>) => void;
} {
  const [state, setState] = useState<WebSocketState>({
    status: "connecting",
    latencyMs: 0,
    reconnectAttempt: 0,
    lastEventAt: null,
    isMockMode: false,
    backendState: null,
  });

  const attemptRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cancelledRef = useRef(false);

  // ── Connect ────────────────────────────────────────────────────────────────

  const connect = useCallback(() => {
    if (cancelledRef.current) return;
    if (!url) {
      setState((s) => ({ ...s, status: fallbackToMock ? "fallback" : "disconnected", isMockMode: fallbackToMock }));
      return;
    }

    const start = Date.now();
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      handleFail();
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      attemptRef.current = 0;
      setState({
        status: "connected",
        latencyMs: Date.now() - start,
        reconnectAttempt: 0,
        lastEventAt: new Date(),
        isMockMode: false,
        backendState: null,
      });

      // Ask for current state immediately
      ws.send(JSON.stringify({ command: "state", params: {} }));
    };

    ws.onmessage = (ev) => {
      let msg: { type: string; data: unknown; timestamp?: string };
      try {
        msg = JSON.parse(ev.data as string);
      } catch {
        return;
      }

      setState((s) => ({ ...s, lastEventAt: new Date() }));

      if (msg.type === "state_update" || msg.type === "step_result") {
        const payload = msg.data as BackendStateUpdate;
        setState((s) => ({ ...s, backendState: payload }));
        onStateUpdate?.(payload);
      }

      if (msg.type === "pong") {
        setState((s) => ({ ...s, latencyMs: Date.now() - start }));
      }
    };

    ws.onclose = () => handleFail();
    ws.onerror  = () => handleFail();
  }, [url, fallbackToMock, onStateUpdate]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleFail() {
    if (cancelledRef.current) return;
    attemptRef.current += 1;
    setState((s) => ({ ...s, status: "disconnected", reconnectAttempt: attemptRef.current }));

    if (attemptRef.current >= maxReconnectAttempts) {
      if (fallbackToMock) {
        setState((s) => ({ ...s, status: "fallback", isMockMode: true }));
      }
      return;
    }
    setTimeout(connect, reconnectDelay);
  }

  // Send a typed command to the backend
  const sendCommand = useCallback(
    (command: string, params: Record<string, unknown> = {}) => {
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command, params }));
      }
    },
    [],
  );

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  useEffect(() => {
    if (typeof window === "undefined") return;
    cancelledRef.current = false;
    connect();

    return () => {
      cancelledRef.current = true;
      if (pingTimerRef.current) clearInterval(pingTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // ── Mock latency jitter when in fallback ───────────────────────────────────
  useEffect(() => {
    if (state.status !== "fallback") return;
    const t = setInterval(() => {
      setState((s) => ({
        ...s,
        latencyMs: 8 + Math.round(Math.random() * 14),
        lastEventAt: new Date(),
      }));
    }, 2000);
    return () => clearInterval(t);
  }, [state.status]);

  return { ...state, sendCommand };
}
