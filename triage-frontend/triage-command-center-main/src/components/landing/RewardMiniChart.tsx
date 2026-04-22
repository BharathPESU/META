import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip } from "recharts";
import { initialMetrics } from "@/lib/simulation";

export function RewardMiniChart() {
  const data = initialMetrics();
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
          <XAxis
            dataKey="episode"
            stroke="var(--text-muted)"
            tick={{ fontFamily: "DM Mono", fontSize: 10 }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="var(--text-muted)"
            tick={{ fontFamily: "DM Mono", fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              fontFamily: "DM Mono",
              fontSize: 11,
            }}
          />
          <Line
            type="monotone"
            dataKey="baselineScore"
            name="Baseline"
            stroke="var(--text-muted)"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive
          />
          <Line
            type="monotone"
            dataKey="rewardScore"
            name="TRIAGE"
            stroke="var(--clinical-blue)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--clinical-blue)" }}
            isAnimationActive
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
