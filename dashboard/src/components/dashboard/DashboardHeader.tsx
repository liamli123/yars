"use client";

import { useState } from "react";

interface Props {
  scrapedAt: string;
  postCount: number;
  commentCount: number;
  subredditCount: number;
}

export default function DashboardHeader({ scrapedAt, postCount, commentCount, subredditCount }: Props) {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const date = new Date(scrapedAt);
  const formatted = date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });

  const stats = [
    { label: "Posts Scraped", value: postCount },
    { label: "Comments", value: commentCount },
    { label: "Subreddits", value: subredditCount },
  ];

  async function triggerScrape() {
    setStatus("loading");
    try {
      const res = await fetch("/api/trigger-scrape", { method: "POST" });
      if (res.ok) {
        setStatus("success");
        setTimeout(() => setStatus("idle"), 5000);
      } else {
        setStatus("error");
        setTimeout(() => setStatus("idle"), 5000);
      }
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 5000);
    }
  }

  return (
    <div className="mb-8">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Reddit Finance Dashboard
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Powered by YARS + DeepSeek AI
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500">
            Last updated: {formatted}
          </div>
          <button
            onClick={triggerScrape}
            disabled={status === "loading"}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              status === "loading"
                ? "bg-gray-700 text-gray-400 cursor-wait"
                : status === "success"
                ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30"
                : status === "error"
                ? "bg-red-600/20 text-red-400 border border-red-500/30"
                : "bg-violet-600/20 text-violet-300 border border-violet-500/30 hover:bg-violet-600/30"
            }`}
          >
            {status === "loading"
              ? "Triggering..."
              : status === "success"
              ? "Scraper triggered!"
              : status === "error"
              ? "Failed - check config"
              : "Refresh Data"}
          </button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 mt-6">
        {stats.map((s) => (
          <div
            key={s.label}
            className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-center"
          >
            <div className="text-2xl font-bold text-white">
              {s.value.toLocaleString()}
            </div>
            <div className="text-xs text-gray-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
