"use client";

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

interface DataPoint {
  subreddit: string;
  score: number;
  comments: number;
  activity: number;
}

export default function SubredditRadar({ data }: { data: DataPoint[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Subreddit Comparison
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Normalized scores, comment engagement, and post activity
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="subreddit" stroke="#9ca3af" fontSize={11} />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            stroke="#4b5563"
            fontSize={10}
          />
          <Radar
            name="Avg Score"
            dataKey="score"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.2}
          />
          <Radar
            name="Avg Comments"
            dataKey="comments"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.2}
          />
          <Radar
            name="Post Activity"
            dataKey="activity"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.2}
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
          <Legend
            wrapperStyle={{ fontSize: "12px", color: "#9ca3af" }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
