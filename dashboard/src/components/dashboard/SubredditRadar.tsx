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
import { SubredditStats } from "@/lib/types";
import { SUBREDDIT_COLORS } from "@/lib/data";

interface Props {
  stats: Record<string, SubredditStats>;
}

export default function SubredditActivity({ stats }: Props) {
  const data = Object.entries(stats).map(([sub, s]) => ({
    name: `r/${sub}`,
    "Avg Upvotes": Math.round(s.avg_score),
    "Avg Comments": Math.round(s.avg_comments),
    "Post Count": s.post_count,
    fill: SUBREDDIT_COLORS[sub] || "#6b7280",
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Subreddit Activity
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Average upvotes, comments, and post count per community
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ left: 10, right: 20, bottom: 10 }}>
          <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} />
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
          <Bar
            dataKey="Avg Upvotes"
            fill="#8b5cf6"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="Avg Comments"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="Post Count"
            fill="#10b981"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
