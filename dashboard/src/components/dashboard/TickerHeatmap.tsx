"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { TickerFactor } from "@/lib/types";

interface Props {
  ticker: string;
  factors: TickerFactor[];
}

export default function TickerHeatmap({ ticker, factors }: Props) {
  const sorted = [...factors].sort((a, b) => b.intensity - a.intensity);

  const data = sorted.map((f) => ({
    factor: f.factor,
    intensity: f.intensity,
    type: f.type,
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-1">
        Sentiment Factors: {ticker}
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Top positive and negative factors being discussed
      </p>
      <ResponsiveContainer width="100%" height={Math.max(500, data.length * 28)}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <XAxis
            type="number"
            domain={[-10, 10]}
            stroke="#4b5563"
            fontSize={12}
            tickCount={11}
          />
          <YAxis
            type="category"
            dataKey="factor"
            stroke="#9ca3af"
            fontSize={11}
            width={180}
            tick={{ fill: "#d1d5db" }}
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
            formatter={(value: any) => [
              `${Math.abs(value)}/10`,
              value > 0 ? "Positive" : "Negative",
            ]}
          />
          <ReferenceLine x={0} stroke="#4b5563" strokeWidth={1} />
          <Bar dataKey="intensity" radius={[4, 4, 4, 4]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={
                  entry.intensity > 0
                    ? `hsl(152, ${50 + entry.intensity * 5}%, ${35 + entry.intensity * 2}%)`
                    : `hsl(0, ${50 + Math.abs(entry.intensity) * 5}%, ${35 + Math.abs(entry.intensity) * 2}%)`
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
