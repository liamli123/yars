"use client";

import { AiAnalysis } from "@/lib/types";

const sentimentConfig = {
  bullish: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", icon: "^" },
  bearish: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30", icon: "v" },
  neutral: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", icon: "~" },
};

export default function AiInsightsPanel({ analysis }: { analysis: AiAnalysis }) {
  const s = analysis.sentiment;
  const cfg = sentimentConfig[s.overall] || sentimentConfig.neutral;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-lg font-semibold text-white">AI Market Analysis</h2>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
          DeepSeek
        </span>
      </div>

      {/* Sentiment Badge */}
      <div className={`inline-flex items-center gap-3 px-4 py-3 rounded-lg border ${cfg.bg} ${cfg.border} mb-6`}>
        <span className={`text-2xl font-bold uppercase tracking-wider ${cfg.color}`}>
          {s.overall}
        </span>
        <div className="h-8 w-px bg-gray-700" />
        <div>
          <div className="text-sm text-gray-300">
            Confidence: <span className={`font-semibold ${cfg.color}`}>{s.confidence}%</span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5 max-w-md">
            {s.reasoning}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Themes */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3">Key Themes</h3>
          <ul className="space-y-2">
            {analysis.themes.map((theme, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-300">
                <span className="text-violet-400 mt-0.5 flex-shrink-0">*</span>
                {theme}
              </li>
            ))}
          </ul>
        </div>

        {/* Tickers to Watch */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3">Tickers to Watch</h3>
          <div className="space-y-3">
            {analysis.tickers_to_watch.map((t, i) => {
              const tcfg = sentimentConfig[t.sentiment] || sentimentConfig.neutral;
              return (
                <div key={i} className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-white font-semibold">${t.ticker}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${tcfg.bg} ${tcfg.color}`}>
                      {t.sentiment}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{t.reason}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Factors & Contrarian Views */}
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Risk Factors</h3>
            <ul className="space-y-2">
              {analysis.risk_factors.map((risk, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-300">
                  <span className="text-red-400 mt-0.5 flex-shrink-0">!</span>
                  {risk}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Contrarian Views</h3>
            <ul className="space-y-2">
              {analysis.contrarian_views.map((view, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-300">
                  <span className="text-amber-400 mt-0.5 flex-shrink-0">?</span>
                  {view}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
