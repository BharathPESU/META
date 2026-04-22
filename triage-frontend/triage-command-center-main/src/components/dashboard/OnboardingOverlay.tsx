import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const STEPS = [
  {
    title: "The Crisis",
    description:
      "A mass casualty event has been triggered. Agents are responding in real time.",
    target: "crisis_header",
  },
  {
    title: "6 AI Agents",
    description:
      "Each agent has a specialist role — ER Triage, ICU, Pharmacy, HR, IT, and a CMO Oversight agent watching everything.",
    target: "agent_grid",
  },
  {
    title: "Patient Board",
    description:
      "Patients color-coded by severity. Watch their status change as agents make decisions.",
    target: "patient_board",
  },
  {
    title: "Reward Score",
    description:
      "This score climbs as agents improve. After DPO training it jumps from 47 to 84.",
    target: "reward_score",
  },
];

const KEY = "triage-onboarded";

export function OnboardingOverlay() {
  const [show, setShow] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (typeof localStorage === "undefined") return;
    if (localStorage.getItem(KEY) === "1") return;
    setShow(true);
  }, []);

  useEffect(() => {
    if (!show) return;
    const t = setTimeout(() => {
      if (step < STEPS.length - 1) setStep((s) => s + 1);
      else dismiss();
    }, 2800);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, step]);

  function dismiss() {
    try {
      localStorage.setItem(KEY, "1");
    } catch {}
    setShow(false);
  }

  if (!show) return null;
  const cur = STEPS[step];

  return (
    <div className="fixed inset-0 z-[55] pointer-events-none">
      <div className="absolute inset-0 bg-black/30 pointer-events-auto" onClick={dismiss} />
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 pointer-events-auto"
      >
        <div
          className="border border-border bg-surface p-5 shadow-2xl"
          style={{ borderRadius: 8, minWidth: 360, maxWidth: 460 }}
        >
          <div className="flex items-center justify-between">
            <div className="font-mono text-[10px] uppercase tracking-widest text-primary">
              Tour · {step + 1} / {STEPS.length}
            </div>
            <button
              onClick={dismiss}
              className="font-mono text-[10px] uppercase tracking-wider text-text-muted hover:text-text-primary"
            >
              Skip
            </button>
          </div>
          <div className="mt-2 font-display text-2xl text-text-primary">{cur.title}</div>
          <div className="mt-2 text-sm text-text-secondary">{cur.description}</div>
          <div className="mt-4 flex gap-1.5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className="h-1 flex-1"
                style={{
                  background:
                    i <= step ? "var(--clinical-blue)" : "var(--border)",
                  borderRadius: 1,
                }}
              />
            ))}
          </div>
        </div>
      </motion.div>
      <style>{`[data-onboarding-target="${cur.target}"] { position: relative; z-index: 56; box-shadow: 0 0 0 3px var(--clinical-blue), 0 0 32px 4px var(--clinical-blue-light); border-radius: 8px; }`}</style>
    </div>
  );
}
