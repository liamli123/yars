"use client";

interface Props {
  scrapedAt: string;
  postCount: number;
  commentCount: number;
  subredditCount: number;
}

export default function DashboardHeader({ scrapedAt, postCount, commentCount, subredditCount }: Props) {
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
        <div className="text-sm text-gray-500">
          Last updated: {formatted}
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
