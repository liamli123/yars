"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SUBREDDIT_COLORS } from "@/lib/data";

interface Props {
  data: Record<string, string | number>[];
  subreddits: string[];
}

export default function SubredditTickerChart({ data, subreddits }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mt-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Ticker Mentions by Subreddit
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Where each ticker is being discussed most
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ left: 10, right: 20, bottom: 10 }}>
          <XAxis dataKey="ticker" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#4b5563" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "13px",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          {subreddits.map((sub) => (
            <Bar
              key={sub}
              dataKey={sub}
              name={`r/${sub}`}
              fill={SUBREDDIT_COLORS[sub] || "#6b7280"}
              radius={[4, 4, 0, 0]}
              stackId="stack"
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
