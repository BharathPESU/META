import type { AgentKey } from "./types";

export const AGENTS: {
  key: AgentKey;
  name: string;
  color: string;
  bg: string;
  role: string;
}[] = [
  {
    key: "CMO_OVERSIGHT",
    name: "CMO OVERSIGHT",
    color: "var(--agent-purple)",
    bg: "var(--agent-purple-light)",
    role: "Meta-agent monitoring all department actions for protocol compliance",
  },
  {
    key: "ER_TRIAGE",
    name: "ER TRIAGE",
    color: "var(--emergency-red)",
    bg: "var(--emergency-red-light)",
    role: "Assigns triage scores and routes incoming patients",
  },
  {
    key: "ICU_MANAGEMENT",
    name: "ICU MANAGEMENT",
    color: "var(--clinical-blue)",
    bg: "var(--clinical-blue-light)",
    role: "Manages bed allocation, ventilator assignments, ICU capacity",
  },
  {
    key: "PHARMACY",
    name: "PHARMACY",
    color: "var(--warning-amber)",
    bg: "var(--warning-amber-light)",
    role: "Drug allocation, stock monitoring, emergency procurement",
  },
  {
    key: "HR_ROSTERING",
    name: "HR ROSTERING",
    color: "#0d9488",
    bg: "#ccfbf1",
    role: "Staff scheduling, shift coverage, fatigue tracking",
  },
  {
    key: "IT_SYSTEMS",
    name: "IT SYSTEMS",
    color: "#6b7280",
    bg: "#f3f4f6",
    role: "EHR sync, insurance verification, data integrity",
  },
];

export const PATIENT_CONDITIONS = [
  "Polytrauma",
  "Cardiac Arrest",
  "Septic Shock",
  "Burns (>40% BSA)",
  "Stroke",
  "Gunshot Wound",
  "Respiratory Failure",
  "Head Trauma",
  "Internal Bleeding",
  "Anaphylaxis",
  "Overdose",
  "Spinal Injury",
  "Acute MI",
  "Pulmonary Embolism",
  "Diabetic Ketoacidosis",
];

export const PATIENT_NAMES = [
  "M. Chen", "J. Rodriguez", "A. Patel", "S. Okonkwo", "R. Müller",
  "L. Tanaka", "K. Singh", "D. Volkov", "E. O'Brien", "N. Hassan",
  "P. Andersson", "T. Nguyen", "F. Rossi", "B. Kowalski", "G. Silva",
  "H. Yamamoto", "I. Petrov", "C. Kim", "V. Reyes", "W. Eriksson",
  "O. Dubois", "Q. Ferreira", "U. Achterberg", "Y. Haddad", "Z. Lindqvist",
  "X. Zhao", "M. Begum", "J. Cohen", "A. Novak", "S. Rasmussen",
];

export const WARDS = ["ER", "ICU", "OR", "WARD-A", "WARD-B", "WARD-C", "TRAUMA"];

export const MESSAGE_TEMPLATES: { type: import("./types").MessageType; from: string; to: string; tpl: string }[] = [
  { type: "HANDOFF", from: "ER_TRIAGE", to: "ICU_MANAGEMENT", tpl: "Transferring {pid}. Diagnosis: {cond}. GCS: 8. BP: 80/50. Immediate OR consult required." },
  { type: "OVERSIGHT", from: "CMO_OVERSIGHT", to: "ER_TRIAGE", tpl: "⚠️ Protocol deviation on {pid}. Triage score mismatch. Reassess immediately." },
  { type: "ALERT", from: "PHARMACY", to: "BROADCAST", tpl: "Epinephrine stock at 12%. Activating emergency procurement. ETA: 45 minutes." },
  { type: "REQUEST", from: "ICU_MANAGEMENT", to: "CMO_OVERSIGHT", tpl: "ICU at 90% capacity. Recommending transfer protocol Alpha-3." },
  { type: "REQUEST", from: "HR_ROSTERING", to: "IT_SYSTEMS", tpl: "Requesting staff availability pull for night shift. 6 nurses needed." },
  { type: "ACTION", from: "IT_SYSTEMS", to: "BROADCAST", tpl: "EHR sync complete. 28 patient records updated. Insurance verification: 21/28 approved." },
  { type: "OVERSIGHT", from: "CMO_OVERSIGHT", to: "BROADCAST", tpl: "Episode performance update. Survival rate: 87%. Compliance: 94%. Reward: 83.2" },
  { type: "REQUEST", from: "ER_TRIAGE", to: "PHARMACY", tpl: "Urgent — {pid} requires O-negative blood. 4 units. Stat." },
  { type: "ACTION", from: "ICU_MANAGEMENT", to: "ER_TRIAGE", tpl: "Bed 7 ready for {pid}. Ventilator pre-configured." },
  { type: "ALERT", from: "ER_TRIAGE", to: "BROADCAST", tpl: "Incoming: 3 patients via ambulance. ETA 4 minutes. {cond} suspected." },
  { type: "HANDOFF", from: "ICU_MANAGEMENT", to: "ER_TRIAGE", tpl: "{pid} stable, downgrading to WARD-A. Bed freed." },
  { type: "OVERSIGHT", from: "CMO_OVERSIGHT", to: "PHARMACY", tpl: "Audit flag: dosage on {pid} exceeds protocol max by 8%. Confirm or revise." },
];

export const BONUS_PRIZES = [
  { sponsor: "Meta PyTorch", req: "Best use of OpenEnv RL training loop", covers: "Custom multi-agent env w/ reward shaping", status: "covered" },
  { sponsor: "HuggingFace", req: "Open-source agent on the Hub", covers: "TRIAGE-CMO model card + dataset published", status: "covered" },
  { sponsor: "Patronus AI", req: "Schema drift / safety monitoring", covers: "CMO Oversight layer flags protocol deviations", status: "covered" },
  { sponsor: "Weights & Biases", req: "Experiment tracking", covers: "Full reward curve + per-agent metrics logged", status: "covered" },
  { sponsor: "Modal", req: "Serverless GPU compute", covers: "Distributed episode rollouts on Modal workers", status: "covered" },
  { sponsor: "Anthropic", req: "Claude as coordinator agent", covers: "Claude 3.5 powers CMO Oversight reasoning", status: "covered" },
  { sponsor: "Mercor", req: "Human-in-the-loop labeling", covers: "Partial — manual triage corrections logged", status: "partial" },
];
