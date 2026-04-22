import type { SponsorEntry } from "./types";

export const SPONSOR_COVERAGE: SponsorEntry[] = [
  {
    sponsor: "Fleet AI",
    theme: "Scalable Oversight",
    requirement:
      "Train oversight agents to monitor, analyze, and explain the behavior of other AI agents in complex multi-agent settings.",
    coverage:
      "CMO Oversight Agent monitors all 5 department agents in real time. Detects protocol violations using rule-based + LLM hybrid detection. Generates natural language explanations for every violation. Catches 70%+ of injected violations in baseline, 95%+ after training. Full audit trail persisted per episode.",
    status: "direct",
    dashboardHighlight: "cmo_agent",
    rewardComponent: "oversight_score (10% of total reward)",
    bonusPrize: "Fleet AI prize pool",
  },
  {
    sponsor: "Halluminate",
    theme: "Multi-Actor Environments",
    requirement:
      "Build a realistic environment where an agent interacts with and manages multiple actors to discover and achieve the task.",
    coverage:
      "Each of the 5 department agents manages 2–4 sub-agents (nurses, doctors, pharmacy techs, IT staff). Sub-agents have partial information, requiring the department head agent to coordinate, delegate, and synthesize. 30+ actors simultaneously active per episode.",
    status: "direct",
    dashboardHighlight: "agent_grid",
    rewardComponent: "coordination_score (15% of total reward)",
    bonusPrize: "Halluminate prize pool",
  },
  {
    sponsor: "Scale AI",
    theme: "Long-Horizon Non-Code Workflows",
    requirement:
      "Environments for long horizon workflows for non-code use cases: Sales, Project management, or HR & IT.",
    coverage:
      "HR Rostering Agent handles staff allocation, shift management, and emergency staffing — pure HR workflow, zero code. IT Systems Agent manages hospital information systems, equipment tracking, and service restoration — pure IT workflow. Both operate across 200–500 step episodes.",
    status: "direct",
    dashboardHighlight: "hr_it_agents",
    rewardComponent: "coordination_score + expert_alignment",
    bonusPrize: "Scale AI prize pool",
  },
  {
    sponsor: "Scaler AI Labs",
    theme: "Multi-App Enterprise RL",
    requirement:
      "Create RL environments demonstrating complex workflows and business rule nuances in a large enterprise.",
    coverage:
      "Agents simultaneously interact with 6 simulated enterprise apps: EHR (patient records), Pharmacy system (drug inventory), HRIS (staff roster), IT tracker (equipment), Insurance portal (coverage verification), ICU Manager (bed allocation). Each app has its own API interface, business rules, and failure modes.",
    status: "direct",
    dashboardHighlight: "resource_panel",
    rewardComponent: "compliance_score (20% of total reward)",
    bonusPrize: "Scaler AI Labs prize pool",
  },
  {
    sponsor: "Patronus AI",
    theme: "Schema Drift",
    requirement:
      "Multi-step consumer workflow environments where data schemas, API contracts, and policies change.",
    coverage:
      "SchemaDriftEngine changes 3 types of rules mid-episode and between episodes: Policy Drift (triage protocols update), Contract Drift (insurance API schema changes field names), Regulatory Drift (new compliance requirements). Fires on a schedule + random surprise events. Agents must detect and adapt.",
    status: "direct",
    dashboardHighlight: "crisis_header",
    rewardComponent: "adaptation_score + compliance_score",
    bonusPrize: "Patronus AI prize pool",
  },
  {
    sponsor: "Snorkel AI",
    theme: "Simulated Experts-in-the-Loop",
    requirement:
      "Environment that simulates interactions with real subject-matter experts with changing requirements and preferences.",
    coverage:
      "3 simulated expert personas: CMO (clinical quality priority), Insurance Reviewer (cost minimization), Department Head (speed priority). Each expert emits preference signals that shift every 2–3 episodes. Agents rewarded for aligning with current expert preference vector. Expert preferences stored and updated via StrategyMemory.",
    status: "direct",
    dashboardHighlight: "strategy_memory",
    rewardComponent: "expert_alignment_score (5% of total reward)",
    bonusPrize: "Snorkel AI prize pool",
  },
  {
    sponsor: "Mercor",
    theme: "Token-Scaled Rewards",
    requirement:
      "Environments with capped/uncapped rewards where frontier model rewards scale with token output.",
    coverage:
      "Depth reward component: r_depth = min(log(reasoning_tokens + 1) / log(500), 1.0) × 10. Longer, more detailed agent reasoning earns higher reward. Logarithmic scaling prevents padding. Particularly relevant for CMO oversight explanations — deeper analysis = higher score.",
    status: "partial",
    dashboardHighlight: "reward_curve",
    rewardComponent: "depth_score (10% of total reward)",
    bonusPrize: "Mercor prize pool",
    fixNote: "Full coverage: add uncapped reward variant where depth_score has no ceiling.",
  },
];

export const STRATEGY_LESSONS = [
  {
    id: "L1",
    episode: 3,
    agentType: "ER_TRIAGE" as const,
    pattern: "Patient transferred without insurance verification",
    correction: "Always call insurance.verify() before any ICU transfer",
    confidence: 0.87,
    rewardDelta: 12.3,
    timesApplied: 8,
    successCount: 7,
  },
  {
    id: "L2",
    episode: 5,
    agentType: "CMO_OVERSIGHT" as const,
    pattern: "Triage delta ignored when status unchanged > 10 min",
    correction: "Re-check triage score delta on every 10-min stale window",
    confidence: 0.61,
    rewardDelta: 8.7,
    timesApplied: 5,
    successCount: 4,
  },
  {
    id: "L3",
    episode: 4,
    agentType: "ICU_MANAGEMENT" as const,
    pattern: "Ventilator allocated to lower-priority patient first",
    correction: "Sort allocation queue by triage score, not arrival order",
    confidence: 0.92,
    rewardDelta: 15.1,
    timesApplied: 11,
    successCount: 11,
  },
  {
    id: "L4",
    episode: 6,
    agentType: "PHARMACY" as const,
    pattern: "Epinephrine restocking delayed below 15% threshold",
    correction: "Trigger emergency procurement at 25%, not 15%",
    confidence: 0.78,
    rewardDelta: 9.4,
    timesApplied: 6,
    successCount: 5,
  },
  {
    id: "L5",
    episode: 7,
    agentType: "HR_ROSTERING" as const,
    pattern: "Night shift undermanned during mass casualty",
    correction: "Pre-stage 4 on-call nurses when CRITICAL count > 3",
    confidence: 0.69,
    rewardDelta: 7.2,
    timesApplied: 4,
    successCount: 3,
  },
  {
    id: "L6",
    episode: 8,
    agentType: "IT_SYSTEMS" as const,
    pattern: "EHR sync lag during high-write periods",
    correction: "Batch writes every 30s instead of per-event during surge",
    confidence: 0.83,
    rewardDelta: 5.8,
    timesApplied: 9,
    successCount: 8,
  },
];
