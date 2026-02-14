"use client";

import { TickerDetail } from "@/lib/types";

interface Props {
  ticker: string;
  detail: TickerDetail;
}

export default function TickerSummary({ ticker, detail }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white mb-1">
            Community Discussion: {ticker}
          </h2>
          <p className="text-xs text-gray-500">
            AI-generated summary from Reddit posts and comments
          </p>
        </div>
        <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
          {detail.mention_count} mention{detail.mention_count !== 1 ? "s" : ""}
        </span>
      </div>
      {detail.mention_count <= 2 && (
        <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3 mb-4">
          <p className="text-xs text-amber-400">
            Low mention count — summary includes general market context to supplement limited Reddit discussion.
          </p>
        </div>
      )}
      <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line max-h-[500px] overflow-y-auto">
        {detail.summary}
      </div>
    </div>
  );
}
