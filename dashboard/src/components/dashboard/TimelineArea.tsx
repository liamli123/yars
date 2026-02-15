"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  time: string;
  posts: number;
  avgScore: number;
}

export default function TimelineArea({ data }: { data: DataPoint[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Post Activity Timeline
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Post volume and average score over time
      </p>
      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="min-w-[500px] px-4 sm:px-0">
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data} margin={{ left: 10, right: 20 }}>
          <defs>
            <linearGradient id="gradPosts" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="time" stroke="#4b5563" fontSize={11} angle={-30} textAnchor="end" height={60} />
          <YAxis yAxisId="left" stroke="#8b5cf6" fontSize={12} />
          <YAxis yAxisId="right" orientation="right" stroke="#10b981" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "13px",
            }}
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="posts"
            name="Posts"
            stroke="#8b5cf6"
            fill="url(#gradPosts)"
            strokeWidth={2}
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="avgScore"
            name="Avg Score"
            stroke="#10b981"
            fill="url(#gradScore)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
