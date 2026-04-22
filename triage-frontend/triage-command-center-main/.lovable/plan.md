
## TRIAGE — Frontend Build Plan

Build the complete TRIAGE hospital crisis simulation frontend on TanStack Start (the project's actual stack). All visual specs, simulation behavior, and components from the brief are preserved — only the routing/layout primitives are translated from Next.js App Router to TanStack file-based routes.

### Foundation
- Add deps: `recharts`, `framer-motion`, `lucide-react` (already present), Google Fonts via `<link>` in `__root.tsx` (Instrument Serif, DM Mono, DM Sans)
- Rewrite `src/styles.css` with the clinical color palette as CSS variables, register them in Tailwind v4 `@theme inline`, set body to DM Sans, define utility classes for Instrument Serif headings and DM Mono data
- Red-cross SVG favicon
- Meta tags: "TRIAGE — AI Hospital Crisis Simulator | Meta PyTorch OpenEnv Hackathon"

### Shared
- `Navbar` — TRIAGE wordmark (Instrument Serif) + red cross SVG, links to Dashboard / Visualizer / GitHub / HuggingFace, sticky, hairline bottom border, clinical-blue active underline
- UI primitives: `StatusBadge` (8px dot + mono text), `MetricCard`, `AgentTag`, `PatientCard`
- `lib/types.ts`, `lib/constants.ts` (agents, conditions, names, message templates)
- `lib/simulation.ts` — deterministic-ish engine: 20–30 patients, ticks every 2s updating 1–3 statuses, generates agent messages every 1.5s, climbs reward 45 → 87 across 10 episodes, tracks ICU beds / ventilators / blood / staff
- `hooks/useSimulation.ts` — exposes `{ patients, agents, messages, metrics, resources, isRunning, episode, step, toggleSimulation, resetSimulation }`

### Page 1 — Landing (`src/routes/index.tsx`)
Replaces the placeholder. Sections: Hero (60/40 split, animated mini patient board on right), Problem Statement (italic pull-quote + 3 problem cards on surface-2), Agent Architecture (pure CSS/Tailwind hierarchy: CMO on top, 5 dept agents row, sub-agent pills, CSS connector lines), Bonus Prizes (7 sponsor cards, 6 covered / 1 partial), Reward Model (mono code block + mini Recharts line), CTA (dark bg, team name ERROR_404_NOT_FOUND).

### Page 2 — Dashboard (`src/routes/dashboard.tsx`) — pitch-critical
Single-viewport, no-scroll layout at 1440px+:
- `CrisisHeader` — pulsing red dot, "MASS CASUALTY EVENT — ACTIVE", episode/step counters, reward score, mono timer
- Left 25%: `AgentStatusGrid` — 6 agent cards (CMO purple, ER red, ICU blue, Pharmacy amber, HR teal, IT gray) with animated thinking pulse on PROCESSING
- Center 50%: tabs for `PatientBoard` (sortable by triage score, Framer Motion row enter + status flash) and `AgentMessageFeed` (auto-scroll, slide-from-right, color-coded left borders by message type, CMO oversight in purple)
- Right 25%: `RewardCurveChart` (Recharts, baseline dashed gray + trained solid blue, draw-on-mount) and `ResourcePanel` (4 gauges, green→amber→red shift)
- `React.memo` on row + message components for smoothness

### Page 3 — Visualizer (`src/routes/visualizer.tsx`) — full spec
- Left 35%: episode slider 1–10, Play/Pause/Step/Reset, speed 0.5×/1×/2×, crisis dropdown, stats (survival %, triage-to-treatment min, compliance %, coordination %, schema drift count)
- Right 65%: hand-drawn SVG floor plan — ED (bottom), ICU (top-left), Wards A/B/C (top-right), Pharmacy (mid-left), OR Suite (mid-right), Admin/IT (bottom-right), corridor lines, patient dots (color-coded circles) and agent diamonds with CSS-transition movement between rooms
- Full-width bottom: `AgentDecisionLog` timeline, outcome color-coded (green optimal / amber suboptimal / red caught-by-oversight)

### Quality bar
- Hairline 1px borders only, 8px radius cards, no gradients, no rounded bubbly UI
- Every numeric value (IDs `#PT-0042`, timestamps, metrics, counters) in DM Mono
- Agent names always uppercase
- Headings font-weight 500, never bold
- Zero TS errors, simulation runs smoothly with 30 patients
