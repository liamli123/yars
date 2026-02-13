export interface Post {
  subreddit: string;
  title: string;
  body: string;
  score: number;
  num_comments: number;
  created_utc: number;
  author: string;
  permalink: string;
  tickers: string[];
}

export interface Comment {
  post_title: string;
  subreddit: string;
  comment: string;
  score: number;
  author: string;
  tickers: string[];
}

export interface SubredditStats {
  post_count: number;
  avg_score: number;
  avg_comments: number;
  total_score: number;
}

export interface TickerToWatch {
  ticker: string;
  sentiment: "bullish" | "bearish" | "neutral";
  reason: string;
}

export interface AiAnalysis {
  sentiment: {
    overall: "bullish" | "bearish" | "neutral";
    confidence: number;
    reasoning: string;
  };
  themes: string[];
  tickers_to_watch: TickerToWatch[];
  risk_factors: string[];
  contrarian_views: string[];
  sector_breakdown: Record<string, number>;
}

export interface DashboardData {
  scraped_at: string;
  subreddits: string[];
  posts: Post[];
  comments: Comment[];
  ticker_mentions: Record<string, number>;
  subreddit_tickers: Record<string, Record<string, number>>;
  subreddit_stats: Record<string, SubredditStats>;
  ai_analysis: AiAnalysis;
}
