"use client";

import { AiAnalysis } from "@/lib/types";

const sentimentConfig = {
  bullish: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
  bearish: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30" },
  neutral: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30" },
};

function getThemeTitle(theme: string | { title: string; explanation: string }): string {
  return typeof theme === "string" ? theme : theme.title;
}

function getThemeExplanation(theme: string | { title: string; explanation: string }): string | null {
  return typeof theme === "string" ? null : theme.explanation;
}

function getRiskTitle(risk: string | { title: string; explanation: string }): string {
  return typeof risk === "string" ? risk : risk.title;
}

function getRiskExplanation(risk: string | { title: string; explanation: string }): string | null {
  return typeof risk === "string" ? null : risk.explanation;
}

function getViewTitle(view: string | { title: string; explanation: string }): string {
  return typeof view === "string" ? view : view.title;
}

function getViewExplanation(view: string | { title: string; explanation: string }): string | null {
  return typeof view === "string" ? null : view.explanation;
}

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
      <div className={`inline-flex items-center gap-4 px-5 py-4 rounded-lg border ${cfg.bg} ${cfg.border} mb-8`}>
        <span className={`text-2xl font-bold uppercase tracking-wider ${cfg.color}`}>
          {s.overall}
        </span>
        <div className="h-10 w-px bg-gray-700" />
        <div>
          <div className="text-sm text-gray-300">
            Confidence: <span className={`font-semibold ${cfg.color}`}>{s.confidence}%</span>
          </div>
          <p className="text-sm text-gray-400 mt-1 max-w-xl leading-relaxed">
            {s.reasoning}
          </p>
        </div>
      </div>

      {/* Tickers to Watch - full width cards */}
      <div className="mb-8">
        <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Tickers to Watch</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
          {analysis.tickers_to_watch.map((t, i) => {
            const tcfg = sentimentConfig[t.sentiment] || sentimentConfig.neutral;
            return (
              <div key={i} className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg font-bold text-white">${t.ticker}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tcfg.bg} ${tcfg.color}`}>
                    {t.sentiment}
                  </span>
                </div>
                <p className="text-sm text-gray-400 leading-relaxed">{t.reason}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Key Themes */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Key Themes</h3>
          <div className="space-y-4">
            {analysis.themes.map((theme, i) => (
              <div key={i}>
                <div className="flex gap-2 items-start">
                  <span className="text-violet-400 mt-0.5 flex-shrink-0 font-bold">{i + 1}.</span>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{getThemeTitle(theme)}</p>
                    {getThemeExplanation(theme) && (
                      <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                        {getThemeExplanation(theme)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Factors */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Risk Factors</h3>
          <div className="space-y-4">
            {analysis.risk_factors.map((risk, i) => (
              <div key={i} className="bg-red-500/5 border border-red-500/10 rounded-lg p-3">
                <div className="flex gap-2 items-start">
                  <span className="text-red-400 mt-0.5 flex-shrink-0">!</span>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{getRiskTitle(risk)}</p>
                    {getRiskExplanation(risk) && (
                      <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                        {getRiskExplanation(risk)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Contrarian Views */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Contrarian Views</h3>
          <div className="space-y-4">
            {analysis.contrarian_views.map((view, i) => (
              <div key={i} className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3">
                <div className="flex gap-2 items-start">
                  <span className="text-amber-400 mt-0.5 flex-shrink-0">?</span>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{getViewTitle(view)}</p>
                    {getViewExplanation(view) && (
                      <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                        {getViewExplanation(view)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
