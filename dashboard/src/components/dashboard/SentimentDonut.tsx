"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  sectorBreakdown: Record<string, number>;
}

const COLORS = [
  "#8b5cf6",
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#06b6d4",
];

export default function SentimentDonut({ sectorBreakdown }: Props) {
  const data = Object.entries(sectorBreakdown)
    .sort(([, a], [, b]) => b - a)
    .map(([name, value]) => ({ name, value }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Sector Distribution
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Mention share by sector across all discussions
      </p>
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <ResponsiveContainer width="100%" height={250} className="sm:!w-[55%]">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={95}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#fff",
                fontSize: "13px",
              }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [
                `${value} (${((Number(value) / total) * 100).toFixed(1)}%)`,
                "Mentions",
              ]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="w-full sm:flex-1 space-y-2">
          {data.map((d, i) => (
            <div key={d.name} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}
              />
              <span className="text-gray-300 flex-1">{d.name}</span>
              <span className="text-gray-500 tabular-nums">
                {((d.value / total) * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
