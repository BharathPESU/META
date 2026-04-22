import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Navbar } from "@/components/nav/Navbar";
import { SPONSOR_COVERAGE } from "@/lib/sponsors";
import { Check, AlertCircle, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/sponsors")({
  head: () => ({
    meta: [
      { title: "Bonus Prize Coverage · TRIAGE" },
      { name: "description", content: "How TRIAGE covers each hackathon sponsor bonus prize." },
      { property: "og:title", content: "TRIAGE Sponsor Coverage Matrix" },
      { property: "og:description", content: "Detailed mapping of TRIAGE features to each sponsor's bonus prize requirements." },
    ],
  }),
  component: SponsorsPage,
});

function SponsorsPage() {
  const [selectedKey, setSelectedKey] = useState(SPONSOR_COVERAGE[0].sponsor);
  const selected = SPONSOR_COVERAGE.find((s) => s.sponsor === selectedKey)!;
  const directs = SPONSOR_COVERAGE.filter((s) => s.status === "direct").length;
  const partials = SPONSOR_COVERAGE.filter((s) => s.status === "partial").length;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="mx-auto max-w-[1440px] px-6 py-10">
        <div className="font-mono text-[11px] uppercase tracking-widest text-primary">
          Q&A weapon · open this when a judge asks "how does this cover X?"
        </div>
        <h1 className="font-display mt-3 text-[44px] leading-tight text-text-primary">
          Bonus Prize Coverage
        </h1>
        <div className="mt-3 font-mono text-[12px] text-text-secondary">
          {SPONSOR_COVERAGE.length} sponsors · {directs} direct · {partials} partial · 0 missed
        </div>

        <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
          {SPONSOR_COVERAGE.map((s) => (
            <SponsorCoverageCard
              key={s.sponsor}
              sponsor={s}
              selected={s.sponsor === selectedKey}
              onSelect={() => setSelectedKey(s.sponsor)}
            />
          ))}
        </div>

        <div
          className="mt-10 grid grid-cols-1 gap-0 border border-border bg-surface lg:grid-cols-[280px_1fr]"
          style={{ borderRadius: 8 }}
        >
          <div className="border-b border-border p-6 lg:border-b-0 lg:border-r">
            <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
              Selected
            </div>
            <h2 className="font-display mt-2 text-3xl text-text-primary">{selected.sponsor}</h2>
            <div className="mt-1 font-mono text-[11px] uppercase tracking-wider text-primary">
              {selected.theme}
            </div>
            <div className="mt-4 space-y-2 font-mono text-[10px] uppercase tracking-wider text-text-muted">
              <div>
                Reward component: <span className="text-text-secondary">{selected.rewardComponent}</span>
              </div>
              <div>
                Bonus prize: <span className="text-text-secondary">{selected.bonusPrize}</span>
              </div>
            </div>
            <a
              href={`/dashboard?highlight=${encodeURIComponent(selected.dashboardHighlight)}`}
              className="mt-6 inline-flex items-center gap-1.5 bg-primary px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-primary-foreground hover:bg-primary-dark"
              style={{ borderRadius: 4 }}
            >
              See it live in Dashboard <ArrowRight className="h-3 w-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 gap-0 md:grid-cols-2">
            <div className="border-b border-border p-6 md:border-b-0 md:border-r">
              <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
                Their Requirement
              </div>
              <p className="mt-3 text-[14px] leading-[1.6] text-text-primary">
                {selected.requirement}
              </p>
            </div>
            <div className="p-6">
              <div className="font-mono text-[10px] uppercase tracking-widest text-stable">
                How TRIAGE Covers It
              </div>
              <p className="mt-3 text-[14px] leading-[1.6] text-text-primary">
                {selected.coverage}
              </p>
              {selected.fixNote && (
                <div
                  className="mt-4 border border-border bg-warning-light p-3 text-[12px] text-text-secondary"
                  style={{ borderRadius: 4, borderLeft: "3px solid var(--warning-amber)" }}
                >
                  <span className="font-mono text-[10px] uppercase tracking-wider text-warning">
                    Gap to close
                  </span>
                  <div className="mt-1">{selected.fixNote}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SponsorCoverageCard({
  sponsor,
  selected,
  onSelect,
}: {
  sponsor: (typeof SPONSOR_COVERAGE)[number];
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`group relative flex flex-col items-start gap-2 border bg-surface p-4 text-left transition-all hover:border-primary ${selected ? "ring-2 ring-primary" : "border-border"}`}
      style={{ borderRadius: 6 }}
    >
      <div className="flex w-full items-center justify-between">
        <div className="font-mono text-[11px] uppercase tracking-wider text-text-primary">
          {sponsor.sponsor}
        </div>
        {sponsor.status === "direct" ? (
          <span
            className="inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[9px] uppercase"
            style={{
              background: "var(--stable-green-light)",
              color: "var(--stable-green)",
              borderRadius: 3,
            }}
          >
            <Check className="h-2.5 w-2.5" /> Direct
          </span>
        ) : (
          <span
            className="inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[9px] uppercase"
            style={{
              background: "var(--warning-amber-light)",
              color: "var(--warning-amber)",
              borderRadius: 3,
            }}
          >
            <AlertCircle className="h-2.5 w-2.5" /> Partial
          </span>
        )}
      </div>
      <div className="text-[11px] text-text-secondary">{sponsor.theme}</div>
    </button>
  );
}
