"use client";

import { useState } from "react";
import { Post } from "@/lib/types";
import { SUBREDDIT_COLORS } from "@/lib/data";

export default function TopPostsTable({ posts }: { posts: Post[] }) {
  const [sortBy, setSortBy] = useState<"score" | "num_comments">("score");
  const sorted = [...posts].sort((a, b) => b[sortBy] - a[sortBy]).slice(0, 25);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Top Posts</h2>
          <p className="text-xs text-gray-500">Top 25 posts by engagement</p>
        </div>
        <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setSortBy("score")}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              sortBy === "score"
                ? "bg-gray-700 text-white"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            By Score
          </button>
          <button
            onClick={() => setSortBy("num_comments")}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              sortBy === "num_comments"
                ? "bg-gray-700 text-white"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            By Comments
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
              <th className="text-left py-3 px-2">#</th>
              <th className="text-left py-3 px-2">Title</th>
              <th className="text-left py-3 px-2">Subreddit</th>
              <th className="text-right py-3 px-2">Score</th>
              <th className="text-right py-3 px-2">Comments</th>
              <th className="text-left py-3 px-2">Tickers</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((post, i) => (
              <tr
                key={i}
                className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
              >
                <td className="py-3 px-2 text-gray-500 tabular-nums">
                  {i + 1}
                </td>
                <td className="py-3 px-2 text-gray-200 max-w-xs truncate">
                  <a
                    href={`https://reddit.com${post.permalink}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-violet-400 transition-colors"
                  >
                    {post.title}
                  </a>
                </td>
                <td className="py-3 px-2">
                  <span
                    className="text-xs px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: `${SUBREDDIT_COLORS[post.subreddit] || "#6b7280"}20`,
                      color: SUBREDDIT_COLORS[post.subreddit] || "#6b7280",
                    }}
                  >
                    r/{post.subreddit}
                  </span>
                </td>
                <td className="py-3 px-2 text-right text-gray-300 tabular-nums font-medium">
                  {post.score.toLocaleString()}
                </td>
                <td className="py-3 px-2 text-right text-gray-400 tabular-nums">
                  {post.num_comments.toLocaleString()}
                </td>
                <td className="py-3 px-2">
                  <div className="flex gap-1 flex-wrap">
                    {post.tickers.slice(0, 3).map((t) => (
                      <span
                        key={t}
                        className="text-xs bg-gray-800 text-emerald-400 px-1.5 py-0.5 rounded"
                      >
                        ${t}
                      </span>
                    ))}
                    {post.tickers.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{post.tickers.length - 3}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
