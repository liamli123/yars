import { NextResponse } from "next/server";

export async function POST() {
  const token = process.env.GITHUB_PAT;
  if (!token) {
    return NextResponse.json(
      { error: "GITHUB_PAT not configured" },
      { status: 500 }
    );
  }

  const owner = process.env.GITHUB_OWNER || "liamli123";
  const repo = process.env.GITHUB_REPO || "yars";

  try {
    const res = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/actions/workflows/scrape.yml/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
        body: JSON.stringify({ ref: "main" }),
      }
    );

    if (res.status === 204) {
      return NextResponse.json({ success: true, message: "Scraper triggered" });
    }

    const body = await res.text();
    return NextResponse.json(
      { error: `GitHub API returned ${res.status}: ${body}` },
      { status: res.status }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
