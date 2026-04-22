import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import type { AgentMessage, KeyMoment, Patient, ReplayEpisode } from "@/lib/types";
import { REPLAY_EPISODES } from "@/lib/replay";
import { initialPatients, makeMessage, tickPatients } from "@/lib/simulation";

export interface ReplayState {
  episode: ReplayEpisode;
  episodes: ReplayEpisode[];
  selectEpisode: (id: string) => void;
  currentStep: number;
  setStep: (n: number) => void;
  isPlaying: boolean;
  togglePlay: () => void;
  speed: number;
  setSpeed: (n: number) => void;
  patientStateAtStep: Patient[];
  messagesAtStep: AgentMessage[];
  rewardAtStep: number;
  keyMoments: KeyMoment[];
  jumpToMoment: (step: number) => void;
}

/** Reconstruct patient/message state for a given step using the seedable simulation. */
function reconstruct(step: number, totalSteps: number, finalReward: number) {
  let patients = initialPatients(24);
  const messages: AgentMessage[] = [];
  for (let s = 1; s <= step; s++) {
    const r = tickPatients(patients);
    patients = r.next;
    if (s % 2 === 0) {
      messages.unshift(makeMessage(patients));
      if (messages.length > 30) messages.pop();
    }
  }
  const reward = +(finalReward * (step / totalSteps)).toFixed(1);
  return { patients, messages, reward };
}

export function useReplay(initialEpisodeId = REPLAY_EPISODES[0].id): ReplayState {
  const [episodeId, setEpisodeId] = useState(initialEpisodeId);
  const episode = useMemo(
    () => REPLAY_EPISODES.find((e) => e.id === episodeId) ?? REPLAY_EPISODES[0],
    [episodeId],
  );
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (timer.current) clearInterval(timer.current);
    if (!isPlaying) return;
    timer.current = setInterval(() => {
      setCurrentStep((s) => {
        if (s >= episode.totalSteps) {
          setIsPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, 200 / speed);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [isPlaying, speed, episode.totalSteps]);

  // Reset step on episode change
  useEffect(() => {
    setCurrentStep(0);
    setIsPlaying(false);
  }, [episodeId]);

  const reconstructed = useMemo(
    () => reconstruct(currentStep, episode.totalSteps, episode.finalReward),
    [currentStep, episode],
  );

  const selectEpisode = useCallback((id: string) => setEpisodeId(id), []);
  const togglePlay = useCallback(() => setIsPlaying((p) => !p), []);
  const jumpToMoment = useCallback((step: number) => setCurrentStep(step), []);

  return {
    episode,
    episodes: REPLAY_EPISODES,
    selectEpisode,
    currentStep,
    setStep: setCurrentStep,
    isPlaying,
    togglePlay,
    speed,
    setSpeed,
    patientStateAtStep: reconstructed.patients,
    messagesAtStep: reconstructed.messages,
    rewardAtStep: reconstructed.reward,
    keyMoments: episode.keyMoments,
    jumpToMoment,
  };
}
