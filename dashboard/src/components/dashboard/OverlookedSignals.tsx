import { OverlookedInsight, Catalyst, CrowdVsNews } from "@/lib/types";

interface Props {
  insights: OverlookedInsight[];
  catalysts: Catalyst[];
  crowdVsNews: CrowdVsNews[];
}

const statusConfig: Record<
  string,
  { label: string; color: string; bg: string; border: string }
> = {
  corroborated: {
    label: "corroborated",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
  },
  "unverified-claim": {
    label: "unverified claim",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
  },
  speculation: {
    label: "speculation",
    color: "text-gray-400",
    bg: "bg-gray-500/10",
    border: "border-gray-500/30",
  },
};

export default function OverlookedSignals({
  insights,
  catalysts,
  crowdVsNews,
}: Props) {
  if (insights.length === 0 && catalysts.length === 0 && crowdVsNews.length === 0) {
    return null;
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6 mt-6">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-semibold text-white">Overlooked Signals</h2>
        <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
          deep analysis
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-6">
        What the community is discussing that mainstream headlines aren&apos;t
        covering — each finding labeled by how well-supported it is
      </p>

      {/* Insight cards */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
          {insights.map((ins, i) => {
            const cfg = statusConfig[ins.status] || statusConfig.speculation;
            return (
              <div
                key={i}
                className="bg-gray-800/30 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="text-sm font-semibold text-white leading-snug">
                    {ins.title}
                  </h3>
                  <span
                    className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border shrink-0 ${cfg.bg} ${cfg.color} ${cfg.border}`}
                  >
                    {cfg.label}
                  </span>
                </div>
                <div className="flex gap-1.5 flex-wrap mb-2">
                  {ins.tickers.map((t) => (
                    <span
                      key={t}
                      className="text-xs bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded"
                    >
                      ${t}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed mb-3">
                  {ins.insight}
                </p>
                <p className="text-xs text-gray-500 leading-relaxed border-l-2 border-gray-700 pl-3 mb-2">
                  {ins.evidence}
                </p>
                <p className="text-xs text-gray-500 italic">
                  Why it&apos;s overlooked: {ins.why_overlooked}
                </p>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Catalysts */}
        {catalysts.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">
              Upcoming Catalysts the Crowd Is Watching
            </h3>
            <div className="space-y-3">
              {catalysts.map((c, i) => (
                <div
                  key={i}
                  className="flex flex-col sm:flex-row gap-2 sm:gap-3 sm:items-start bg-gray-800/30 border border-gray-800 rounded-lg p-3"
                >
                  <span className="text-xs font-semibold text-gray-300 bg-gray-800 px-2 py-1 rounded shrink-0 self-start">
                    {c.when}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm text-gray-200">
                      <span className="text-violet-300 font-medium">
                        ${c.ticker}
                      </span>{" "}
                      — {c.event}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {c.expected_impact}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Crowd vs News */}
        {crowdVsNews.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">
              Where the Crowd Disagrees with the News
            </h3>
            <div className="space-y-3">
              {crowdVsNews.map((c, i) => (
                <div
                  key={i}
                  className="bg-gray-800/30 border border-gray-800 rounded-lg p-3"
                >
                  <span className="text-sm font-semibold text-violet-300">
                    ${c.ticker}
                  </span>
                  <div className="mt-2 space-y-1.5 text-xs leading-relaxed">
                    <p>
                      <span className="text-gray-500 uppercase tracking-wider mr-1">
                        News says:
                      </span>
                      <span className="text-gray-300">{c.news_narrative}</span>
                    </p>
                    <p>
                      <span className="text-gray-500 uppercase tracking-wider mr-1">
                        Crowd says:
                      </span>
                      <span className="text-gray-300">{c.crowd_view}</span>
                    </p>
                    <p>
                      <span className="text-gray-400 uppercase tracking-wider mr-1">
                        Verdict:
                      </span>
                      <span className="text-gray-400 italic">
                        {c.who_is_right}
                      </span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
