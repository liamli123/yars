"use client";

import { useState } from "react";
import TickerBarChart from "./TickerBarChart";
import TickerSummary from "./TickerSummary";
import TickerHeatmap from "./TickerHeatmap";
import { TickerDetail } from "@/lib/types";

interface TickerChartDataPoint {
  ticker: string;
  mentions: number;
}

interface Props {
  chartData: TickerChartDataPoint[];
  tickerDetails: Record<string, TickerDetail>;
}

export default function TickerDetailSection({ chartData, tickerDetails }: Props) {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  function handleTickerClick(ticker: string) {
    setSelectedTicker((prev) => (prev === ticker ? null : ticker));
  }

  // Strip $ prefix for lookup in tickerDetails
  const symbol = selectedTicker?.startsWith("$")
    ? selectedTicker.slice(1)
    : selectedTicker;
  const detail = symbol ? tickerDetails[symbol] || null : null;

  return (
    <>
      <TickerBarChart
        data={chartData}
        selectedTicker={selectedTicker}
        onTickerClick={handleTickerClick}
      />

      {selectedTicker && detail && (
        <div className="lg:col-span-2 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TickerSummary ticker={selectedTicker} detail={detail} />
          <TickerHeatmap ticker={selectedTicker} factors={detail.factors} />
        </div>
      )}

      {selectedTicker && !detail && (
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p className="text-gray-500 text-sm">
            No detailed analysis available for {selectedTicker}. Run the scraper to generate ticker details.
          </p>
        </div>
      )}
    </>
  );
}
