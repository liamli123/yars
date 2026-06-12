"use client";

import { useState } from "react";
import { Post } from "@/lib/types";
import TopPostsTable from "./TopPostsTable";

export default function RawMessages({ posts }: { posts: Post[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-6">
      <button
        onClick={() => setOpen(!open)}
        className="w-full bg-gray-900 border border-gray-800 rounded-xl px-6 py-4 flex items-center justify-between hover:border-gray-700 transition-colors"
      >
        <span className="text-sm font-medium text-gray-300">
          Raw messages ({posts.length.toLocaleString()})
        </span>
        <span className="text-xs text-gray-500">
          {open ? "▲ Hide" : "▼ Show"}
        </span>
      </button>
      {open && <TopPostsTable posts={posts} />}
    </div>
  );
}
