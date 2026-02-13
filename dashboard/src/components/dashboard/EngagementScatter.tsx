"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SUBREDDIT_COLORS } from "@/lib/data";

interface DataPoint {
  title: string;
  score: number;
  comments: number;
  subreddit: string;
}

export default function EngagementScatter({
  data,
  subreddits,
}: {
  data: DataPoint[];
  subreddits: string[];
}) {
  const grouped: Record<string, DataPoint[]> = {};
  subreddits.forEach((sub) => {
    grouped[sub] = data.filter((d) => d.subreddit === sub);
  });

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Post Engagement
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Score vs comment count per post, colored by subreddit
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ bottom: 10, left: 10, right: 20 }}>
          <XAxis
            type="number"
            dataKey="score"
            name="Score"
            stroke="#4b5563"
            fontSize={12}
            label={{
              value: "Score",
              position: "insideBottom",
              offset: -5,
              style: { fill: "#6b7280", fontSize: 11 },
            }}
          />
          <YAxis
            type="number"
            dataKey="comments"
            name="Comments"
            stroke="#4b5563"
            fontSize={12}
            label={{
              value: "Comments",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              style: { fill: "#6b7280", fontSize: 11 },
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "13px",
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any, name: any) => [value, name]}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(_: any, payload: any) => {
              if (payload && payload[0]) {
                const d = payload[0].payload as DataPoint;
                return d.title;
              }
              return "";
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          {subreddits.map((sub) => (
            <Scatter
              key={sub}
              name={`r/${sub}`}
              data={grouped[sub] || []}
              fill={SUBREDDIT_COLORS[sub] || "#6b7280"}
              opacity={0.8}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
