import { DashboardData } from "@/lib/types";
import {
  getTickerChartData,
  getSubredditRadarData,
  getEngagementData,
  getTimelineData,
  getSubredditTickerData,
} from "@/lib/data";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import TickerBarChart from "@/components/dashboard/TickerBarChart";
import SubredditRadar from "@/components/dashboard/SubredditRadar";
import SentimentDonut from "@/components/dashboard/SentimentDonut";
import EngagementScatter from "@/components/dashboard/EngagementScatter";
import TimelineArea from "@/components/dashboard/TimelineArea";
import SubredditTickerChart from "@/components/dashboard/SubredditTickerChart";
import AiInsightsPanel from "@/components/dashboard/AiInsightsPanel";
import TopPostsTable from "@/components/dashboard/TopPostsTable";
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
        postCount={data.posts.length}
        commentCount={data.comments.length}
        subredditCount={data.subreddits.length}
      />

      {/* AI Insights */}
      <AiInsightsPanel analysis={data.ai_analysis} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <TickerBarChart data={getTickerChartData(data)} />
        <SubredditRadar data={getSubredditRadarData(data)} />
        <SentimentDonut sectorBreakdown={data.ai_analysis.sector_breakdown} />
        <EngagementScatter
          data={getEngagementData(data)}
          subreddits={data.subreddits}
        />
      </div>

      {/* Timeline - full width */}
      <div className="mt-6">
        <TimelineArea data={getTimelineData(data)} />
      </div>

      {/* Subreddit Ticker Comparison - full width */}
      <SubredditTickerChart
        data={getSubredditTickerData(data)}
        subreddits={data.subreddits}
      />

      {/* Posts Table */}
      <TopPostsTable posts={data.posts} />

      {/* Footer */}
      <footer className="mt-8 py-4 border-t border-gray-800 text-center text-xs text-gray-600">
        Built with YARS (Yet Another Reddit Scraper) + DeepSeek AI
      </footer>
    </main>
  );
}
