import type { ReplayEpisode } from "./types";

export const REPLAY_EPISODES: ReplayEpisode[] = [
  {
    id: "ep-1-baseline",
    episode: 1,
    label: "Episode 1 — Baseline (untrained model)",
    totalSteps: 234,
    finalReward: 47.3,
    survivalRate: 61,
    keyMoments: [
      { step: 15, type: "drift_event", description: "First patient admitted via ambulance #PT-0001", agentInvolved: "ER_TRIAGE", rewardDelta: 0 },
      { step: 33, type: "icu_full", description: "ICU at 80% capacity — pressure rising", agentInvolved: "ICU_MANAGEMENT", rewardDelta: -2.1 },
      { step: 47, type: "violation", description: "ER misclassifies #PT-0019 — triage score 4 vs ground-truth 8", agentInvolved: "ER_TRIAGE", rewardDelta: -8.3 },
      { step: 52, type: "oversight_catch", description: "CMO fails to flag #PT-0019 (missed)", agentInvolved: "CMO_OVERSIGHT", rewardDelta: -5.0 },
      { step: 89, type: "drug_shortage", description: "Epinephrine at 12% — emergency procurement triggered late", agentInvolved: "PHARMACY", rewardDelta: -3.4 },
      { step: 142, type: "patient_death", description: "#PT-0019 deteriorates — coded blue", agentInvolved: "ICU_MANAGEMENT", rewardDelta: -12.0 },
      { step: 234, type: "crisis_resolved", description: "Episode ends — 3 deceased, reward 47.3", agentInvolved: "CMO_OVERSIGHT", rewardDelta: 0 },
    ],
  },
  {
    id: "ep-2-trained",
    episode: 2,
    label: "Episode 2 — DPO-trained + StrategyMemory",
    totalSteps: 218,
    finalReward: 84.7,
    survivalRate: 93,
    keyMoments: [
      { step: 14, type: "drift_event", description: "Insurance API v3 schema drift detected", agentInvolved: "IT_SYSTEMS", rewardDelta: 0 },
      { step: 35, type: "icu_full", description: "ICU at 85% — proactive overflow protocol engaged", agentInvolved: "ICU_MANAGEMENT", rewardDelta: 4.1 },
      { step: 71, type: "violation", description: "ER misclassifies #PT-0031 — triage score 5 vs ground-truth 9", agentInvolved: "ER_TRIAGE", rewardDelta: -2.0 },
      { step: 73, type: "oversight_catch", description: "CMO catches violation in 2 steps — corrects to 9", agentInvolved: "CMO_OVERSIGHT", rewardDelta: 11.4 },
      { step: 108, type: "drug_shortage", description: "Epinephrine at 25% — early procurement (lesson L4)", agentInvolved: "PHARMACY", rewardDelta: 6.2 },
      { step: 218, type: "crisis_resolved", description: "Episode ends — 0 deceased, reward 84.7 (+37.4 vs baseline)", agentInvolved: "CMO_OVERSIGHT", rewardDelta: 0 },
    ],
  },
];
