"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface DataPoint {
  ticker: string;
  mentions: number;
}

export default function TickerBarChart({ data }: { data: DataPoint[] }) {
  const maxMentions = Math.max(...data.map((d) => d.mentions));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Top Ticker Mentions
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Most discussed stocks across all subreddits
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <XAxis type="number" stroke="#4b5563" fontSize={12} />
          <YAxis
            type="category"
            dataKey="ticker"
            stroke="#9ca3af"
            fontSize={12}
            width={55}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "13px",
            }}
          />
          <Bar dataKey="mentions" radius={[0, 6, 6, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={`hsl(${150 - (entry.mentions / maxMentions) * 100}, 80%, ${45 + (entry.mentions / maxMentions) * 15}%)`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
