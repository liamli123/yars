import { DashboardData } from "@/lib/types";
import { getTimelineData, getSubredditTickerData } from "@/lib/data";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import OverlookedSignals from "@/components/dashboard/OverlookedSignals";
import BuzzBoard from "@/components/dashboard/BuzzBoard";
import DiscussionDigest from "@/components/dashboard/DiscussionDigest";
import SentimentDonut from "@/components/dashboard/SentimentDonut";
import TimelineArea from "@/components/dashboard/TimelineArea";
import SubredditTickerChart from "@/components/dashboard/SubredditTickerChart";
import AiInsightsPanel from "@/components/dashboard/AiInsightsPanel";
import RawMessages from "@/components/dashboard/RawMessages";
import { readFileSync } from "fs";
import path from "path";

function loadDashboardData(): DashboardData {
  const filePath = path.join(process.cwd(), "public", "data", "dashboard_data.json");
  const raw = readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as DashboardData;
}

export default function Home() {
  const data = loadDashboardData();

  return (
    <main className="min-h-screen p-4 sm:p-6 lg:p-8 max-w-[1400px] mx-auto">
      <DashboardHeader
        scrapedAt={data.scraped_at}
        messageCount={data.posts.length}
        tickerCount={Object.keys(data.ticker_mentions).length}
        sourceCount={data.subreddits.length}
      />

      {/* Deep analysis: what the community knows that the news doesn't */}
      <OverlookedSignals
        insights={data.ai_analysis.overlooked_insights || []}
        catalysts={data.ai_analysis.catalysts || []}
        crowdVsNews={data.ai_analysis.crowd_vs_news || []}
      />

      {/* AI market overview */}
      <AiInsightsPanel
        analysis={data.ai_analysis}
        tickerDetails={data.ticker_details || {}}
      />

      {/* Per-ticker buzz cards */}
      <BuzzBoard
        tickerStats={data.ticker_stats || {}}
        tickerDetails={data.ticker_details || {}}
      />

      {/* AI digest of all collected messages */}
      <DiscussionDigest
        digest={data.ai_analysis.discussion_digest || []}
        yahooTrending={data.yahoo_trending}
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <TimelineArea data={getTimelineData(data)} />
        <SentimentDonut sectorBreakdown={data.ai_analysis.sector_breakdown} />
      </div>

      <SubredditTickerChart
        data={getSubredditTickerData(data)}
        subreddits={data.subreddits}
      />

      {/* Raw messages, collapsed by default */}
      <RawMessages posts={data.posts} />

      {/* Footer */}
      <footer className="mt-8 py-4 border-t border-gray-800 text-center text-xs text-gray-600">
        Data: ApeWisdom (Reddit) + Stocktwits + Yahoo Finance · AI: DeepSeek
      </footer>
    </main>
  );
}
