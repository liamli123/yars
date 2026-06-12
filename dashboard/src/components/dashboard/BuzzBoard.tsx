"use client";

import { useState } from "react";
import { TickerStat, TickerDetail } from "@/lib/types";
import TickerSummary from "./TickerSummary";
import TickerHeatmap from "./TickerHeatmap";

interface Props {
  tickerStats: Record<string, TickerStat>;
  tickerDetails: Record<string, TickerDetail>;
}

function ChangeArrow({ now, before }: { now: number; before: number }) {
  const diff = now - before;
  if (diff === 0 || before === 0) {
    return <span className="text-gray-500 text-xs">–</span>;
  }
  const pct = Math.round((diff / before) * 100);
  return diff > 0 ? (
    <span className="text-emerald-400 text-xs font-semibold">
      ▲ +{pct}%
    </span>
  ) : (
    <span className="text-red-400 text-xs font-semibold">▼ {pct}%</span>
  );
}

function SentimentBar({ bullish, bearish }: { bullish: number; bearish: number }) {
  const total = bullish + bearish;
  if (total === 0) {
    return (
      <div className="h-1.5 rounded-full bg-gray-700/60" title="No sentiment tags" />
    );
  }
  const bullPct = (bullish / total) * 100;
  return (
    <div
      className="h-1.5 rounded-full bg-red-500/70 overflow-hidden flex"
      title={`${bullish} bullish / ${bearish} bearish`}
    >
      <div
        className="h-full bg-emerald-500 rounded-l-full"
        style={{ width: `${bullPct}%` }}
      />
    </div>
  );
}

export default function BuzzBoard({ tickerStats, tickerDetails }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  const tickers = Object.entries(tickerStats).sort(
    ([, a], [, b]) => b.mentions - a.mentions
  );

  if (tickers.length === 0) return null;

  const detail = selected ? tickerDetails[selected] || null : null;

  return (
    <div className="mt-6">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Today&apos;s Buzz Board
          </h2>
          <p className="text-xs text-gray-500">
            Most-discussed stocks · mention change vs previous 24h · community
            sentiment (green = bullish, red = bearish) · click a card for the
            full AI deep-dive
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {tickers.map(([ticker, s]) => {
          const isSelected = selected === ticker;
          const rankMove = s.rank_24h_ago > 0 ? s.rank_24h_ago - s.rank : 0;
          return (
            <button
              key={ticker}
              onClick={() => setSelected(isSelected ? null : ticker)}
              className={`text-left bg-gray-900 border rounded-xl p-4 transition-all hover:border-violet-500/40 hover:-translate-y-0.5 ${
                isSelected
                  ? "border-violet-500/60 shadow-lg shadow-violet-500/10"
                  : "border-gray-800"
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <div>
                  <span className="text-xl font-bold text-white">${ticker}</span>
                  <span className="ml-2 text-xs text-gray-500 align-middle">
                    {s.name.length > 28 ? `${s.name.slice(0, 28)}…` : s.name}
                  </span>
                </div>
                <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full shrink-0">
                  #{s.rank}
                  {rankMove > 0 && (
                    <span className="text-emerald-400 ml-1">↑{rankMove}</span>
                  )}
                  {rankMove < 0 && (
                    <span className="text-red-400 ml-1">↓{-rankMove}</span>
                  )}
                </span>
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-2xl font-bold text-violet-300 tabular-nums">
                  {s.mentions.toLocaleString()}
                </span>
                <span className="text-xs text-gray-500">mentions</span>
                <ChangeArrow now={s.mentions} before={s.mentions_24h_ago} />
              </div>
              <SentimentBar bullish={s.bullish} bearish={s.bearish} />
              {s.blurb && (
                <p className="text-sm text-gray-400 leading-relaxed mt-3">
                  {s.blurb}
                </p>
              )}
              {tickerDetails[ticker] && (
                <p className="text-xs text-violet-400/70 mt-2">
                  {isSelected ? "▲ Hide deep-dive" : "▼ AI deep-dive"}
                </p>
              )}
            </button>
          );
        })}
      </div>

      {selected && detail && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <TickerSummary ticker={`$${selected}`} detail={detail} />
          <TickerHeatmap ticker={`$${selected}`} factors={detail.factors} />
        </div>
      )}
    </div>
  );
}
