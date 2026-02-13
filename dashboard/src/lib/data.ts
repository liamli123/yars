import { DashboardData } from "./types";

export function getTickerChartData(data: DashboardData) {
  return Object.entries(data.ticker_mentions)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 15)
    .map(([ticker, mentions]) => ({ ticker: `$${ticker}`, mentions }));
}

export function getSubredditRadarData(data: DashboardData) {
  const stats = Object.entries(data.subreddit_stats);
  const maxScore = Math.max(...stats.map(([, s]) => s.avg_score));
  const maxComments = Math.max(...stats.map(([, s]) => s.avg_comments));
  const maxPosts = Math.max(...stats.map(([, s]) => s.post_count));

  return stats.map(([sub, s]) => ({
    subreddit: `r/${sub}`,
    score: Math.round((s.avg_score / maxScore) * 100),
    comments: Math.round((s.avg_comments / maxComments) * 100),
    activity: Math.round((s.post_count / maxPosts) * 100),
  }));
}

export function getEngagementData(data: DashboardData) {
  return data.posts.map((p) => ({
    title: p.title.slice(0, 40),
    score: p.score,
    comments: p.num_comments,
    subreddit: p.subreddit,
  }));
}

export function getTimelineData(data: DashboardData) {
  const hourBuckets: Record<string, { count: number; totalScore: number }> = {};
  data.posts.forEach((p) => {
    if (!p.created_utc) return;
    const date = new Date(p.created_utc * 1000);
    const key = `${(date.getMonth() + 1).toString().padStart(2, "0")}/${date.getDate().toString().padStart(2, "0")} ${date.getHours().toString().padStart(2, "0")}:00`;
    if (!hourBuckets[key]) hourBuckets[key] = { count: 0, totalScore: 0 };
    hourBuckets[key].count++;
    hourBuckets[key].totalScore += p.score;
  });
  return Object.entries(hourBuckets)
    .map(([time, d]) => ({
      time,
      posts: d.count,
      avgScore: Math.round(d.totalScore / d.count),
    }))
    .sort((a, b) => a.time.localeCompare(b.time));
}

export function getSubredditTickerData(data: DashboardData) {
  // Get top 10 global tickers
  const topTickers = Object.entries(data.ticker_mentions)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([t]) => t);

  return topTickers.map((ticker) => {
    const row: Record<string, string | number> = { ticker: `$${ticker}` };
    data.subreddits.forEach((sub) => {
      row[sub] = data.subreddit_tickers[sub]?.[ticker] || 0;
    });
    return row;
  });
}

export function getSectorData(data: DashboardData) {
  const sectors = data.ai_analysis?.sector_breakdown || {};
  return Object.entries(sectors)
    .sort(([, a], [, b]) => b - a)
    .map(([sector, count]) => ({ sector, count }));
}

export const SUBREDDIT_COLORS: Record<string, string> = {
  wallstreetbets: "#8b5cf6",
  stocks: "#3b82f6",
  investing: "#10b981",
  options: "#f59e0b",
  StockMarket: "#ef4444",
};
