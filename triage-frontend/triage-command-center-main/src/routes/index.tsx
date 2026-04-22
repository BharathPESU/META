import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Check, AlertTriangle, Brain, Network, RefreshCcw } from "lucide-react";
import { Navbar } from "@/components/nav/Navbar";
import { MiniPatientBoard } from "@/components/landing/MiniPatientBoard";
import { RewardMiniChart } from "@/components/landing/RewardMiniChart";
import { AGENTS, BONUS_PRIZES } from "@/lib/constants";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TRIAGE — AI Hospital Crisis Simulator | Meta PyTorch OpenEnv Hackathon" },
      {
        name: "description",
        content:
          "Multi-agent hospital crisis simulation where specialized AI agents coordinate triage, ICU, pharmacy and staffing during mass casualty events.",
      },
      { property: "og:title", content: "TRIAGE — Can AI save lives under pressure?" },
      {
        property: "og:description",
        content:
          "A multi-agent hospital simulation environment built for the Meta PyTorch OpenEnv Hackathon 2025.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <Hero />
      <ProblemStatement />
      <AgentArchitecture />
      <BonusPrizes />
      <RewardModel />
      <CTASection />
    </div>
  );
}

function Hero() {
  return (
    <section className="border-b border-border">
      <div className="mx-auto grid max-w-[1440px] grid-cols-1 gap-12 px-6 py-20 lg:grid-cols-12 lg:py-28">
        <div className="lg:col-span-7">
          <div className="font-mono text-[11px] uppercase tracking-widest text-primary">
            Meta PyTorch OpenEnv Hackathon · 2025
          </div>
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="font-display mt-5 text-[64px] leading-[1.05] text-text-primary"
          >
            Can <em className="italic">AI</em> save lives <br /> under pressure?
          </motion.h1>
          <p className="mt-6 max-w-xl text-[20px] leading-[1.5] text-text-secondary">
            TRIAGE is a multi-agent hospital crisis simulation environment where specialized AI
            agents autonomously manage mass casualty events — coordinating triage, ICU
            allocation, pharmacy, and staff under life-or-death time pressure.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 text-sm text-primary-foreground hover:bg-primary-dark"
            >
              View Live Demo <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#"
              className="inline-flex items-center gap-2 rounded-md border border-border-strong bg-surface px-5 py-3 text-sm text-text-primary hover:border-primary"
            >
              Read the Paper
            </a>
          </div>
          <div className="mt-10 flex flex-wrap gap-2">
            {[
              ["6", "Bonus Prizes"],
              ["4", "AI Themes"],
              ["90/100", "Projected Score"],
              ["7", "Agent Types"],
            ].map(([n, l]) => (
              <div
                key={l}
                className="flex items-center gap-2 border border-border bg-surface px-3 py-2"
                style={{ borderRadius: 6 }}
              >
                <span className="font-mono text-sm text-text-primary">{n}</span>
                <span className="text-[11px] uppercase tracking-wider text-text-muted">{l}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="lg:col-span-5">
          <MiniPatientBoard />
        </div>
      </div>
    </section>
  );
}

function ProblemStatement() {
  const cards = [
    { icon: Network, title: "No shared world model", body: "Agents act in isolation. None can see the full hospital state at once." },
    { icon: AlertTriangle, title: "Cannot recover from cascading failures", body: "One drug shortage triggers staffing panic, then ICU overload. Nobody adapts." },
    { icon: RefreshCcw, title: "Zero cross-episode learning", body: "Today's mistakes do not improve tomorrow's response. Every disaster is the first one." },
  ];
  return (
    <section className="border-b border-border bg-surface-2">
      <div className="mx-auto max-w-[1440px] px-6 py-24">
        <div className="font-mono text-[11px] uppercase tracking-widest text-text-muted">
          01 · The Problem
        </div>
        <h2 className="font-display mt-3 text-[32px] text-text-primary">The Problem</h2>
        <div className="mt-12 grid grid-cols-1 gap-12 lg:grid-cols-12">
          <div className="lg:col-span-6">
            <p className="font-display text-[28px] italic leading-[1.35] text-text-primary">
              "AI agents handle isolated tasks well. They fail catastrophically at coordinated,
              high-stakes, multi-agent crisis response."
            </p>
            <p className="mt-6 text-sm text-text-secondary">
              Current LLM agents are evaluated on single-turn tasks. Real crises are
              multi-domain, time-pressured, and require continuous coordination across
              departments with conflicting priorities.
            </p>
          </div>
          <div className="lg:col-span-6 grid grid-cols-1 gap-3">
            {cards.map((c) => (
              <div
                key={c.title}
                className="flex gap-4 border border-border bg-surface p-5"
                style={{ borderRadius: 8 }}
              >
                <div
                  className="flex h-10 w-10 shrink-0 items-center justify-center border border-border"
                  style={{ borderRadius: 6, background: "var(--surface-2)" }}
                >
                  <c.icon className="h-5 w-5 text-text-secondary" />
                </div>
                <div>
                  <div className="text-sm font-medium text-text-primary">{c.title}</div>
                  <div className="mt-1 text-sm text-text-secondary">{c.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function AgentArchitecture() {
  const cmo = AGENTS[0];
  const dept = AGENTS.slice(1);
  const subAgents: Record<string, string[]> = {
    ER_TRIAGE: ["INTAKE", "SCORING", "ROUTING"],
    ICU_MANAGEMENT: ["BEDS", "VENT-ALLOC"],
    PHARMACY: ["STOCK", "DISPENSE", "PROCURE"],
    HR_ROSTERING: ["SCHEDULE", "FATIGUE"],
    IT_SYSTEMS: ["EHR-SYNC", "INSURANCE"],
  };

  return (
    <section className="border-b border-border">
      <div className="mx-auto max-w-[1440px] px-6 py-24">
        <div className="font-mono text-[11px] uppercase tracking-widest text-text-muted">
          02 · Architecture
        </div>
        <h2 className="font-display mt-3 text-[32px] text-text-primary">Agent Architecture</h2>
        <p className="mt-3 max-w-2xl text-sm text-text-secondary">
          A meta-agent oversees five department agents, each managing a specialized sub-agent
          pool. All communication is observable and logged.
        </p>

        <div className="mt-14">
          {/* CMO */}
          <div className="mx-auto max-w-md">
            <AgentCard
              name={cmo.name}
              role={cmo.role}
              color={cmo.color}
              bg={cmo.bg}
              wide
            />
          </div>

          {/* Connector */}
          <div className="mx-auto my-2 h-8 w-px" style={{ background: "var(--border-strong)" }} />

          {/* Department row */}
          <div className="relative">
            <div
              className="absolute left-1/2 top-0 hidden h-px -translate-x-1/2 lg:block"
              style={{ background: "var(--border-strong)", width: "85%" }}
            />
            <div className="grid grid-cols-2 gap-3 pt-4 md:grid-cols-3 lg:grid-cols-5">
              {dept.map((a) => (
                <div key={a.key} className="flex flex-col gap-2">
                  <div className="mx-auto -mt-4 hidden h-4 w-px lg:block" style={{ background: "var(--border-strong)" }} />
                  <AgentCard name={a.name} role={a.role} color={a.color} bg={a.bg} />
                  <div className="mt-2 flex flex-wrap justify-center gap-1.5">
                    {subAgents[a.key]?.map((s) => (
                      <span
                        key={s}
                        className="border border-border bg-surface px-2 py-1 font-mono text-[10px] tracking-wider text-text-secondary"
                        style={{ borderRadius: 4 }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function AgentCard({
  name,
  role,
  color,
  bg,
  wide,
}: {
  name: string;
  role: string;
  color: string;
  bg: string;
  wide?: boolean;
}) {
  return (
    <div
      className={`relative border border-border bg-surface p-4 ${wide ? "py-5" : ""}`}
      style={{ borderRadius: 8, borderLeft: `3px solid ${color}` }}
    >
      <div className="flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
        <div className="font-mono text-[11px] tracking-wider" style={{ color }}>
          {name}
        </div>
      </div>
      <div className="mt-2 text-[12px] leading-snug text-text-secondary">{role}</div>
      <div
        className="absolute right-2 top-2 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider"
        style={{ background: bg, color, borderRadius: 3 }}
      >
        agent
      </div>
    </div>
  );
}

function BonusPrizes() {
  return (
    <section className="border-b border-border bg-surface-2">
      <div className="mx-auto max-w-[1440px] px-6 py-24">
        <div className="font-mono text-[11px] uppercase tracking-widest text-text-muted">
          03 · Sponsors
        </div>
        <h2 className="font-display mt-3 text-[32px] text-text-primary">Bonus Prize Coverage</h2>
        <div className="mt-12 grid grid-cols-1 gap-3 md:grid-cols-2">
          {BONUS_PRIZES.map((p) => (
            <div
              key={p.sponsor}
              className="group flex gap-4 border border-border bg-surface p-5 transition-colors hover:border-primary"
              style={{ borderRadius: 8 }}
            >
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-[11px] uppercase tracking-wider text-text-primary">
                    {p.sponsor}
                  </div>
                  {p.status === "covered" ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 font-mono text-[10px]"
                      style={{ background: "var(--stable-green-light)", color: "var(--stable-green)", borderRadius: 4 }}
                    >
                      <Check className="h-3 w-3" /> COVERED
                    </span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 font-mono text-[10px]"
                      style={{ background: "var(--warning-amber-light)", color: "var(--warning-amber)", borderRadius: 4 }}
                    >
                      PARTIAL
                    </span>
                  )}
                </div>
                <div className="mt-2 text-sm text-text-primary">{p.req}</div>
                <div className="mt-1 text-xs text-text-secondary">{p.covers}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function RewardModel() {
  return (
    <section className="border-b border-border">
      <div className="mx-auto max-w-[1440px] px-6 py-24">
        <div className="font-mono text-[11px] uppercase tracking-widest text-text-muted">
          04 · Reward
        </div>
        <h2 className="font-display mt-3 text-[32px] text-text-primary">Reward Model</h2>
        <div className="mt-12 grid grid-cols-1 gap-10 lg:grid-cols-2">
          <div>
            <div
              className="border border-border bg-text-primary p-6 font-mono text-[13px] leading-[1.7] text-white"
              style={{ borderRadius: 8 }}
            >
              <div><span style={{ color: "#7DD3FC" }}>Sprint Score</span> ={"  "}</div>
              <div className="pl-6">
                (<span style={{ color: "#FCD34D" }}>0.30</span>) × <span style={{ color: "#A5F3FC" }}>task_completion_rate</span>
              </div>
              <div className="pl-6">
                + (<span style={{ color: "#FCD34D" }}>0.25</span>) × <span style={{ color: "#A5F3FC" }}>patient_survival_rate</span>
              </div>
              <div className="pl-6">
                + (<span style={{ color: "#FCD34D" }}>0.20</span>) × <span style={{ color: "#A5F3FC" }}>regulatory_compliance</span>
              </div>
              <div className="pl-6">
                + (<span style={{ color: "#FCD34D" }}>0.15</span>) × <span style={{ color: "#A5F3FC" }}>coordination_efficiency</span>
              </div>
              <div className="pl-6">
                + (<span style={{ color: "#FCD34D" }}>0.10</span>) × <span style={{ color: "#A5F3FC" }}>oversight_catch_rate</span>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-2 text-xs text-text-secondary">
              <Brain className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <span>
                Weights tuned via PPO across 10,000 episodes. Oversight catch rate intentionally
                rewarded — encourages the CMO agent to flag rather than ignore protocol breaches.
              </span>
            </div>
          </div>
          <div className="border border-border bg-surface p-5" style={{ borderRadius: 8 }}>
            <div className="mb-2 flex items-center justify-between">
              <div className="font-mono text-[11px] uppercase tracking-wider text-text-muted">
                Reward Curve · 10 episodes
              </div>
              <div className="font-mono text-xs text-stable">+96% vs baseline</div>
            </div>
            <RewardMiniChart />
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="bg-text-primary text-white">
      <div className="mx-auto max-w-[1440px] px-6 py-24">
        <h2 className="font-display max-w-3xl text-[48px] leading-[1.1] text-white">
          Built for the Grand Finale. <em className="italic text-white/80">Ready to train.</em>
        </h2>
        <p className="mt-6 max-w-2xl text-white/70">
          TRIAGE ships as a PyTorch OpenEnv-compatible environment, a Claude-powered oversight
          agent, and a fully observable simulation with reproducible reward curves.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          {[
            { label: "GitHub", href: "#", v: "github.com/error404/triage" },
            { label: "HuggingFace", href: "#", v: "huggingface.co/error404/triage-cmo" },
            { label: "YouTube Demo", href: "#", v: "youtu.be/triage-demo" },
          ].map((l) => (
            <a
              key={l.label}
              href={l.href}
              className="block border border-white/15 p-5 transition-colors hover:border-white/40"
              style={{ borderRadius: 8 }}
            >
              <div className="font-mono text-[10px] uppercase tracking-widest text-white/50">
                {l.label}
              </div>
              <div className="mt-2 font-mono text-sm text-white">{l.v}</div>
            </a>
          ))}
        </div>
        <div className="mt-16 flex items-center justify-between border-t border-white/10 pt-6 text-xs">
          <div className="font-mono uppercase tracking-widest text-white/50">
            Team · ERROR_404_NOT_FOUND
          </div>
          <div className="font-mono text-white/50">© 2025 · Meta PyTorch OpenEnv Hackathon</div>
        </div>
      </div>
    </section>
  );
}
