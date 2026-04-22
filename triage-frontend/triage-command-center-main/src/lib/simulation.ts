import type {
  AgentMessage,
  AgentState,
  EpisodeMetrics,
  MessageType,
  Patient,
  PatientStatus,
  Resources,
  DecisionLogEntry,
} from "./types";
import { AGENTS, MESSAGE_TEMPLATES, PATIENT_CONDITIONS, PATIENT_NAMES, WARDS } from "./constants";

// Seedable PRNG so SSR + first client paint are identical (no hydration mismatch).
let seed = 1337;
function rand(): number {
  // Mulberry32
  let t = (seed += 0x6d2b79f5);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
function resetSeed(s = 1337) {
  seed = s;
}

let pidCounter = 1;
let mid = 1;

function pick<T>(arr: T[]): T {
  return arr[Math.floor(rand() * arr.length)];
}

function pad(n: number, w = 4) {
  return String(n).padStart(w, "0");
}

// Use a fixed epoch for initial timestamps so SSR == client.
const EPOCH = new Date("2025-01-01T08:00:00Z");

export function makePatient(): Patient {
  const triageScore = Math.floor(rand() * 10) + 1;
  const status: PatientStatus =
    triageScore >= 8 ? "CRITICAL" : triageScore >= 5 ? "SERIOUS" : "STABLE";
  return {
    id: `#PT-${pad(pidCounter++)}`,
    name: pick(PATIENT_NAMES),
    age: 18 + Math.floor(rand() * 70),
    condition: pick(PATIENT_CONDITIONS),
    status,
    ward: pick(WARDS),
    triageScore,
    assignedAgent: pick(AGENTS).name,
    admittedAt: EPOCH,
    lastUpdated: EPOCH,
  };
}

export function initialPatients(n = 24): Patient[] {
  resetSeed(1337);
  pidCounter = 1;
  return Array.from({ length: n }, () => makePatient());
}

export function initialAgents(): AgentState[] {
  return AGENTS.map((a) => ({
    key: a.key,
    name: a.name,
    status: "ACTIVE",
    currentAction: "Monitoring incoming queue",
    messagesSent: 0,
  }));
}

export function initialResources(): Resources {
  return {
    icuBeds: { used: 14, total: 20 },
    ventilators: { used: 9, total: 15 },
    bloodSupply: 78,
    staffOnDuty: { used: 38, total: 45 },
  };
}

export function initialMetrics(): EpisodeMetrics[] {
  const baseline = [42, 44, 41, 45, 43, 46, 44, 45, 43, 47];
  const trained = [45, 52, 58, 63, 69, 74, 78, 82, 85, 87];
  return baseline.map((b, i) => ({
    episode: i + 1,
    baselineScore: b,
    rewardScore: trained[i],
    survivalRate: 65 + i * 2.5,
    complianceScore: 70 + i * 2.4,
    stepsToResolution: 320 - i * 20,
  }));
}

// After first paint, switch to Math.random for live runtime variety.
function rrand() {
  return Math.random();
}
function rpick<T>(arr: T[]): T {
  return arr[Math.floor(rrand() * arr.length)];
}

export function tickPatients(patients: Patient[]): { next: Patient[]; flashed: string[] } {
  const next = [...patients];
  const flashed: string[] = [];
  const updates = 1 + Math.floor(rrand() * 3);
  for (let i = 0; i < updates; i++) {
    const idx = Math.floor(rrand() * next.length);
    const p = next[idx];
    const flow: PatientStatus[] = ["CRITICAL", "SERIOUS", "STABLE", "DISCHARGED"];
    const cur = flow.indexOf(p.status);
    if (cur === -1) continue;
    const direction = rrand() < 0.75 ? 1 : -1;
    const nIdx = Math.max(0, Math.min(flow.length - 1, cur + direction));
    const newStatus = flow[nIdx];
    if (newStatus !== p.status) {
      next[idx] = {
        ...p,
        status: newStatus,
        lastUpdated: new Date(),
        triageScore:
          newStatus === "STABLE"
            ? Math.max(1, p.triageScore - 2)
            : newStatus === "DISCHARGED"
              ? 1
              : p.triageScore,
      };
      flashed.push(p.id);
    }
  }
  // occasionally move a patient between wards (drives floor-plan animation)
  if (rrand() < 0.35 && next.length) {
    const idx = Math.floor(rrand() * next.length);
    const p = next[idx];
    const candidates = WARDS.filter((w) => w !== p.ward);
    next[idx] = { ...p, ward: rpick(candidates), lastUpdated: new Date() };
    flashed.push(p.id);
  }
  // occasionally admit a new patient
  if (rrand() < 0.18 && next.length < 32) {
    const np = {
      ...makePatient(),
      id: `#PT-${pad(pidCounter++)}`,
      admittedAt: new Date(),
      lastUpdated: new Date(),
    };
    next.unshift(np);
    flashed.push(np.id);
  }
  return { next, flashed };
}

export function makeMessage(patients: Patient[]): AgentMessage {
  const t = rpick(MESSAGE_TEMPLATES);
  const p = patients.length ? rpick(patients) : null;
  const content = t.tpl
    .replace("{pid}", p?.id ?? "#PT-0001")
    .replace("{cond}", p?.condition ?? "Polytrauma");
  return {
    id: `m-${mid++}`,
    from: t.from.replace(/_/g, " "),
    to: t.to.replace(/_/g, " "),
    content,
    type: t.type as MessageType,
    timestamp: new Date(),
    patientId: p?.id,
  };
}

export function makeDecision(patients: Patient[]): DecisionLogEntry {
  const a = rpick(AGENTS);
  const p = patients.length ? rpick(patients) : null;
  const r = rrand();
  const outcome: DecisionLogEntry["outcome"] =
    r < 0.7 ? "OPTIMAL" : r < 0.92 ? "SUBOPTIMAL" : "ERROR";
  const actions = [
    "Reallocated bed",
    "Triage score revised",
    "Transferred to ICU",
    "Escalated to OR",
    "Drug dosage adjusted",
    "Staff reassigned",
    "Discharge approved",
  ];
  return {
    id: `d-${mid++}`,
    agent: a.name,
    action: rpick(actions),
    patientId: p?.id ?? "#PT-0001",
    outcome,
    timestamp: new Date(),
  };
}

export function tickResources(r: Resources): Resources {
  const jitter = (n: number, max: number) =>
    Math.max(0, Math.min(max, n + (rrand() < 0.5 ? -1 : 1) * (rrand() < 0.4 ? 1 : 0)));
  return {
    icuBeds: { ...r.icuBeds, used: jitter(r.icuBeds.used, r.icuBeds.total) },
    ventilators: { ...r.ventilators, used: jitter(r.ventilators.used, r.ventilators.total) },
    bloodSupply: Math.max(20, Math.min(100, r.bloodSupply + (rrand() < 0.5 ? -1 : 1))),
    staffOnDuty: { ...r.staffOnDuty, used: jitter(r.staffOnDuty.used, r.staffOnDuty.total) },
  };
}

export function tickAgents(agents: AgentState[], lastMsg?: AgentMessage): AgentState[] {
  return agents.map((a) => {
    const isActor = lastMsg && a.name === lastMsg.from;
    const status = isActor
      ? "PROCESSING"
      : rrand() < 0.15
        ? "WAITING"
        : "ACTIVE";
    return {
      ...a,
      status,
      messagesSent: isActor ? a.messagesSent + 1 : a.messagesSent,
      currentAction: isActor && lastMsg ? lastMsg.content.slice(0, 60) : a.currentAction,
    };
  });
}
