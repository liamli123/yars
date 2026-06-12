#!/usr/bin/env python3
"""Stock buzz scraper.

Answers "which stocks is the internet talking about most, and why?"
without scraping Reddit directly (Reddit blocks most IPs now):

- ApeWisdom   - ticker mention counts aggregated across Reddit finance subs
- Stocktwits  - trending tickers + recent messages, many tagged bullish/bearish
- Yahoo       - trending tickers by search/view interest

Optionally runs DeepSeek AI analysis over the collected data, then writes
dashboard/public/data/dashboard_data.json for the Next.js dashboard.

No credentials required. Set DEEPSEEK_API_KEY to enable the AI sections.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# Emoji-safe output on consoles that default to non-UTF-8 codecs (e.g. GBK)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

TOP_TICKERS = 50      # tickers tracked from ApeWisdom
DETAIL_TICKERS = 12   # tickers that get Stocktwits messages + AI deep-dives

# Stocktwits sits behind Cloudflare, which fingerprints python-requests and
# blocks it from datacenter IPs (e.g. GitHub Actions). curl_cffi impersonates
# a real Chrome browser at the TLS level and usually passes.
try:
    from curl_cffi import requests as cffi_requests
    session = cffi_requests.Session(impersonate="chrome")
    print("(using curl_cffi browser impersonation)")
except ImportError:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT


def fetch_json(url, what):
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"   ✗ {what} failed: {e}")
        return None


def fetch_apewisdom():
    """Top Reddit-mentioned tickers, aggregated by apewisdom.io."""
    data = fetch_json(
        "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1",
        "ApeWisdom",
    )
    if not data:
        return []
    results = []
    for item in data.get("results", [])[:TOP_TICKERS]:
        try:
            results.append({
                "ticker": item["ticker"],
                "name": item.get("name", ""),
                "mentions": int(item.get("mentions") or 0),
                "upvotes": int(item.get("upvotes") or 0),
                "rank": int(item.get("rank") or 0),
                "rank_24h_ago": int(item.get("rank_24h_ago") or 0),
                "mentions_24h_ago": int(item.get("mentions_24h_ago") or 0),
            })
        except (TypeError, ValueError):
            continue
    return results


def fetch_stocktwits_trending():
    data = fetch_json(
        "https://api.stocktwits.com/api/2/trending/symbols.json",
        "Stocktwits trending",
    )
    if not data:
        return []
    return [s["symbol"] for s in data.get("symbols", []) if s.get("symbol")]


def fetch_stocktwits_messages(ticker, pages=2):
    """Recent discussion messages for one ticker (paginated)."""
    raw_messages = []
    max_cursor = None
    for _ in range(pages):
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        if max_cursor:
            url += f"?max={max_cursor}"
        data = fetch_json(url, f"Stocktwits stream for {ticker}")
        if not data:
            break
        raw_messages.extend(data.get("messages", []))
        cursor = data.get("cursor") or {}
        max_cursor = cursor.get("max")
        if not cursor.get("more") or not max_cursor:
            break
        time.sleep(0.5)

    messages = []
    for msg in raw_messages:
        body = msg.get("body", "")
        if not body:
            continue
        sentiment = (
            (msg.get("entities") or {}).get("sentiment") or {}
        ).get("basic", "")
        created = msg.get("created_at", "")
        try:
            created_utc = datetime.strptime(
                created, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            created_utc = 0
        symbols = [s.get("symbol") for s in msg.get("symbols", []) if s.get("symbol")]
        messages.append({
            "id": msg.get("id", 0),
            "body": body,
            "author": (msg.get("user") or {}).get("username", ""),
            "likes": int(((msg.get("likes") or {}).get("total")) or 0),
            "created_utc": created_utc,
            "sentiment": sentiment,  # "Bullish", "Bearish" or ""
            "symbols": symbols or [ticker],
        })
    return messages


def fetch_yahoo_news(ticker, count=8):
    """Mainstream news headlines for a ticker, used as a contrast signal."""
    data = fetch_json(
        f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount={count}",
        f"Yahoo news for {ticker}",
    )
    if not data:
        return []
    return [
        {"title": n.get("title", ""), "publisher": n.get("publisher", "")}
        for n in data.get("news", [])
        if n.get("title")
    ]


def fetch_yahoo_trending():
    data = fetch_json(
        "https://query1.finance.yahoo.com/v1/finance/trending/US?count=20",
        "Yahoo trending",
    )
    if not data:
        return []
    try:
        quotes = data["finance"]["result"][0]["quotes"]
    except (KeyError, IndexError, TypeError):
        return []
    return [q["symbol"] for q in quotes if q.get("symbol")]


def sentiment_ratio(messages):
    bullish = sum(1 for m in messages if m["sentiment"] == "Bullish")
    bearish = sum(1 for m in messages if m["sentiment"] == "Bearish")
    return bullish, bearish


def make_deepseek_client():
    from openai import OpenAI

    # Clear proxy env vars that httpx picks up (socks:// not supported)
    env_backup = {}
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                "http_proxy", "https_proxy", "all_proxy"):
        if key in os.environ:
            env_backup[key] = os.environ.pop(key)
    try:
        return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    finally:
        os.environ.update(env_backup)


def deepseek_json(client, prompt, max_tokens, retries=2, model="deepseek-chat",
                  json_mode=True):
    last_error = None
    for attempt in range(retries + 1):
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except ValueError as e:
            last_error = e
            print(f"   ⚠ Malformed JSON from DeepSeek (attempt {attempt + 1}), retrying...")
    raise last_error


def get_overlooked_insights(apewisdom, ticker_messages, news_by_ticker):
    """Deep, critical pass: what does the community know that the news doesn't?

    Uses deepseek-reasoner (thinks before answering) with a skeptical-analyst
    prompt, fed ALL collected messages plus mainstream headlines per ticker
    so it can surface the gap between the two.
    """
    if not DEEPSEEK_API_KEY:
        print("   ⚠ DEEPSEEK_API_KEY not set, skipping overlooked insights")
        return None
    try:
        client = make_deepseek_client()
    except ImportError:
        print("   ⚠ openai package not installed")
        return None

    print("\n🧠 Running deep analysis (deepseek-reasoner, this takes a few minutes)...")

    mentions_by_ticker = {t["ticker"]: t for t in apewisdom}
    context = {}
    for ticker, messages in ticker_messages.items():
        stats = mentions_by_ticker.get(ticker, {})
        # Most-liked + most recent messages: popular ones show consensus,
        # recent ones catch breaking chatter the like-counts haven't caught up to
        by_likes = sorted(messages, key=lambda m: m["likes"], reverse=True)[:15]
        by_recency = sorted(messages, key=lambda m: m["created_utc"], reverse=True)[:10]
        seen_ids = set()
        sample = []
        for m in by_likes + by_recency:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                sample.append({
                    "text": m["body"][:250],
                    "likes": m["likes"],
                    "tag": m["sentiment"],
                })
        context[ticker] = {
            "reddit_mentions_24h": stats.get("mentions", 0),
            "reddit_mentions_prev_24h": stats.get("mentions_24h_ago", 0),
            "mainstream_headlines": news_by_ticker.get(ticker, []),
            "user_messages": sample,
        }

    prompt = f"""You are a skeptical buy-side analyst hunting for an edge. Below is, per ticker: Reddit mention stats, current MAINSTREAM news headlines, and raw USER MESSAGES from Stocktwits.

Your job is to find the information gap: specific, concrete things users are discussing that the mainstream headlines do NOT cover, or where the community's read contradicts the headlines. Ignore generic hype ("to the moon", "this will 10x") - hunt for specifics: supply-chain details, channel checks, product issues, insider/employee-sounding claims, unusual options activity, dates of upcoming events, regulatory chatter, short-interest mechanics, fund-flow observations.

DATA:
{json.dumps(context, indent=1)}

Return JSON with these exact keys:

- "overlooked_insights": array of 6-10 objects, the BEST information-gap findings, each with:
  - "title": short punchy label (4-8 words)
  - "tickers": array of ticker symbols it concerns
  - "insight": 2-4 sentences. Be SPECIFIC - names, numbers, dates, mechanisms. Plain English.
  - "evidence": 1-2 sentences describing exactly what in the user messages supports this (paraphrase or short quote)
  - "status": one of "corroborated" (multiple independent users or matches a headline detail), "unverified-claim" (specific but single-source), "speculation" (plausible theory, no hard evidence)
  - "why_overlooked": 1 sentence on why mainstream coverage misses or underplays this

- "catalysts": array of upcoming events users mention, each with "ticker", "event" (what happens), "when" (date or timeframe as users state it, e.g. "June 18 Fed meeting", "next week"), and "expected_impact" (1 sentence)

- "crowd_vs_news": array of 2-4 objects where community sentiment clearly DISAGREES with the mainstream narrative, each with "ticker", "news_narrative" (1 sentence), "crowd_view" (1 sentence), "who_is_right" (1-2 sentences of your own critical judgment)

Rules:
- Quality over quantity: a vague insight is worthless, drop it
- Never invent facts not present in the data; if users claim something unverifiable, label it honestly
- Plain English, no jargon without explanation
- Return ONLY valid JSON, no markdown"""

    try:
        result = deepseek_json(
            client, prompt, max_tokens=8000,
            model="deepseek-reasoner", json_mode=False, retries=1,
        )
        print("   ✓ Deep analysis complete (reasoner)")
        return result
    except Exception as e:
        print(f"   ⚠ Reasoner failed ({e}), falling back to deepseek-chat...")
    try:
        result = deepseek_json(client, prompt, max_tokens=6000)
        print("   ✓ Deep analysis complete (chat fallback)")
        return result
    except Exception as e:
        print(f"   ✗ Deep analysis failed: {e}")
        return None


def get_ai_analysis(apewisdom, ticker_messages, yahoo_trending):
    """Overall market analysis via DeepSeek."""
    if not DEEPSEEK_API_KEY:
        print("   ⚠ DEEPSEEK_API_KEY not set, skipping AI analysis")
        return None
    try:
        client = make_deepseek_client()
    except ImportError:
        print("   ⚠ openai package not installed. Run: pip install openai")
        return None

    print("\n🤖 Running DeepSeek AI analysis...")

    top_mentions = [
        {
            "ticker": t["ticker"], "name": t["name"], "mentions": t["mentions"],
            "mentions_24h_ago": t["mentions_24h_ago"],
            "rank": t["rank"], "rank_24h_ago": t["rank_24h_ago"],
        }
        for t in apewisdom[:20]
    ]

    sentiment_summary = {}
    sample_messages = {}
    for ticker, messages in ticker_messages.items():
        bullish, bearish = sentiment_ratio(messages)
        sentiment_summary[ticker] = {
            "bullish_tags": bullish, "bearish_tags": bearish,
            "messages_sampled": len(messages),
        }
        top_msgs = sorted(messages, key=lambda m: m["likes"], reverse=True)[:3]
        sample_messages[ticker] = [m["body"][:200] for m in top_msgs]

    prompt = f"""Analyze this snapshot of stock discussion across the internet and provide investment insights. Write in plain, conversational English that a regular investor can understand - no jargon without explanation.

Top tickers by Reddit mention count (via ApeWisdom aggregator), with 24h changes:
{json.dumps(top_mentions, indent=2)}

Stocktwits community sentiment tags (authors label their own posts bullish/bearish):
{json.dumps(sentiment_summary, indent=2)}

Most-liked recent Stocktwits messages per ticker:
{json.dumps(sample_messages, indent=2)}

Tickers trending on Yahoo Finance (by search/view interest):
{json.dumps(yahoo_trending)}

Provide your analysis as JSON with these exact keys:

- "sentiment": object with "overall" (one of "bullish", "bearish", "neutral"), "confidence" (0-100), and "reasoning" (2-3 sentences in plain English explaining why the market mood leans this way)

- "themes": array of 4-6 objects, each with "title" (short label, 3-6 words) and "explanation" (2-3 sentences in plain English describing what people are talking about and why it matters for investors)

- "tickers_to_watch": array of 5 objects, each with "ticker" (string), "sentiment" ("bullish"/"bearish"/"neutral"), and "reason" (2-3 sentences in plain English explaining why this stock is worth watching right now, what the online community thinks, and what could move the price). IMPORTANT: Only pick tickers that actually appear in the data above. Do NOT recommend tickers from your general knowledge that are not present in this data.

- "risk_factors": array of 3-4 objects, each with "title" (short label) and "explanation" (2-3 sentences in plain English explaining the risk and how it could impact regular investors)

- "contrarian_views": array of 2-3 objects, each with "title" (short label) and "explanation" (2-3 sentences in plain English describing what the minority thinks and why their argument has some merit)

- "sector_breakdown": object mapping sector names to approximate mention counts based on the tickers above (e.g. "Technology": 45)

- "discussion_digest": array of exactly 3 paragraph strings (3-5 sentences each) summarizing what the community is talking about overall today, in plain conversational English. Be specific and critical: include actual numbers, names and dates from the data. Never write generic filler like "investors are excited" - say WHO is bullish on WHAT, WHY, and what the skeptics counter with. Paragraph 1: the biggest story/mover. Paragraph 2: other notable discussions. Paragraph 3: where the crowd disagrees with itself, and what that tension means.

- "ticker_blurbs": object mapping EVERY ticker symbol that appears in the Stocktwits sentiment data above to a 1-2 sentence plain-English summary of what people are saying about that stock right now

Return ONLY valid JSON, no markdown."""

    try:
        analysis = deepseek_json(client, prompt, max_tokens=6000)
        print("   ✓ AI analysis complete")
        return analysis
    except Exception as e:
        print(f"   ✗ AI analysis failed: {e}")
        return None


def get_ticker_details(apewisdom, ticker_messages):
    """Per-ticker ~500 word summaries and sentiment factors via DeepSeek."""
    if not DEEPSEEK_API_KEY:
        print("   ⚠ DEEPSEEK_API_KEY not set, skipping ticker details")
        return {}
    try:
        client = make_deepseek_client()
    except ImportError:
        print("   ⚠ openai package not installed")
        return {}

    mentions_by_ticker = {t["ticker"]: t for t in apewisdom}
    tickers = list(ticker_messages.keys())
    if not tickers:
        print("   ⚠ No tickers found, skipping ticker details")
        return {}

    print(f"\n🔍 Generating details for {len(tickers)} tickers...")

    all_details = {}
    batch_size = 2
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_context = {}
        for ticker in batch:
            messages = ticker_messages[ticker]
            bullish, bearish = sentiment_ratio(messages)
            stats = mentions_by_ticker.get(ticker, {})
            top_msgs = sorted(messages, key=lambda m: m["likes"], reverse=True)[:10]
            batch_context[ticker] = {
                "reddit_mentions_24h": stats.get("mentions", 0),
                "reddit_mentions_previous_24h": stats.get("mentions_24h_ago", 0),
                "reddit_rank": stats.get("rank", 0),
                "stocktwits_bullish_tags": bullish,
                "stocktwits_bearish_tags": bearish,
                "messages": [
                    {"text": m["body"][:300], "likes": m["likes"],
                     "sentiment_tag": m["sentiment"]}
                    for m in top_msgs
                ],
            }
        print(f"   Processing batch: {', '.join(batch)}...")

        prompt = f"""For each of the following stock tickers, analyze the online community discussion (Reddit mention stats + Stocktwits messages) and provide:
1. A ~500-word summary in plain, conversational English about what people are saying, why the stock is getting attention, and what investors should know
2. Exactly 10 positive factors and 10 negative factors being discussed

Here is the data for each ticker:
{json.dumps(batch_context, indent=2)}

Return JSON with this exact structure (one entry per ticker):
{{
  "TICKER_SYMBOL": {{
    "summary": "~500 word plain English summary of community discussion...",
    "factors": [
      {{"factor": "Short description of positive factor", "type": "positive", "intensity": 8}},
      {{"factor": "Short description of negative factor", "type": "negative", "intensity": -7}}
    ]
  }}
}}

Rules:
- intensity ranges from 1 to 10 for positive factors, -1 to -10 for negative factors
- Each ticker MUST have exactly 10 positive factors and 10 negative factors (20 total)
- For tickers with few messages, supplement with general market context about that company
- Write summaries in plain English a regular investor can understand
- Factor descriptions should be concise (5-15 words each)
- Return ONLY valid JSON, no markdown"""

        try:
            batch_details = deepseek_json(client, prompt, max_tokens=6000)
            for ticker in batch:
                if ticker in batch_details:
                    batch_details[ticker]["mention_count"] = (
                        mentions_by_ticker.get(ticker, {}).get("mentions", 0)
                    )
            all_details.update(batch_details)
            print(f"   ✓ Got details for: {', '.join(batch_details.keys())}")
        except Exception as e:
            print(f"   ✗ Batch failed ({', '.join(batch)}): {e}")

        time.sleep(1)

    print(f"   ✓ Ticker details generated for {len(all_details)} tickers total")
    return all_details


def build_dashboard_data(apewisdom, ticker_messages, yahoo_trending, ai_analysis,
                         ticker_details, insights=None):
    sources = ["reddit", "stocktwits"]

    # Per-ticker buzz stats for the dashboard's ticker cards
    blurbs = (ai_analysis or {}).pop("ticker_blurbs", {}) or {}
    mentions_by_ticker = {t["ticker"]: t for t in apewisdom}
    ticker_stats = {}
    for ticker, messages in ticker_messages.items():
        bullish, bearish = sentiment_ratio(messages)
        stats = mentions_by_ticker.get(ticker, {})
        ticker_stats[ticker] = {
            "name": stats.get("name", ""),
            "mentions": stats.get("mentions", 0),
            "mentions_24h_ago": stats.get("mentions_24h_ago", 0),
            "rank": stats.get("rank", 0),
            "rank_24h_ago": stats.get("rank_24h_ago", 0),
            "upvotes": stats.get("upvotes", 0),
            "bullish": bullish,
            "bearish": bearish,
            "message_count": len(messages),
            "blurb": blurbs.get(ticker, ""),
        }

    # Posts list = Stocktwits messages, shaped like the dashboard's Post type
    posts = []
    for ticker, messages in ticker_messages.items():
        for m in messages:
            author = m["author"]
            posts.append({
                "subreddit": "stocktwits",
                "title": m["body"][:200],
                "body": m["body"][:500],
                "score": m["likes"],
                "num_comments": 0,
                "created_utc": m["created_utc"],
                "author": author,
                "permalink": f"https://stocktwits.com/{author}/message/{m['id']}",
                "tickers": m["symbols"][:5],
            })

    ticker_mentions = {t["ticker"]: t["mentions"] for t in apewisdom}

    stocktwits_counts = {
        ticker: len(messages) for ticker, messages in ticker_messages.items()
    }
    subreddit_tickers = {
        "reddit": dict(list(ticker_mentions.items())[:20]),
        "stocktwits": stocktwits_counts,
    }

    total_likes = sum(p["score"] for p in posts)
    subreddit_stats = {
        "reddit": {
            "post_count": sum(ticker_mentions.values()),
            "avg_score": round(
                sum(t["upvotes"] for t in apewisdom) / max(len(apewisdom), 1), 1
            ),
            "avg_comments": 0,
            "total_score": sum(t["upvotes"] for t in apewisdom),
        },
        "stocktwits": {
            "post_count": len(posts),
            "avg_score": round(total_likes / max(len(posts), 1), 1),
            "avg_comments": 0,
            "total_score": total_likes,
        },
    }

    if ai_analysis is None:
        ai_analysis = {
            "sentiment": {"overall": "neutral", "confidence": 0,
                          "reasoning": "AI analysis unavailable"},
            "themes": [],
            "tickers_to_watch": [],
            "risk_factors": [],
            "contrarian_views": [],
            "sector_breakdown": {},
            "discussion_digest": [],
        }

    if insights:
        ai_analysis["overlooked_insights"] = insights.get("overlooked_insights", [])
        ai_analysis["catalysts"] = insights.get("catalysts", [])
        ai_analysis["crowd_vs_news"] = insights.get("crowd_vs_news", [])

    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "subreddits": sources,
        "posts": posts,
        "comments": [],
        "ticker_mentions": ticker_mentions,
        "ticker_stats": ticker_stats,
        "subreddit_tickers": subreddit_tickers,
        "subreddit_stats": subreddit_stats,
        "yahoo_trending": yahoo_trending,
        "ai_analysis": ai_analysis,
        "ticker_details": ticker_details or {},
    }


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Stock Buzz Scraper (ApeWisdom + Stocktwits + Yahoo)")
    print("=" * 70)

    print("\n[STEP 1] Fetching Reddit ticker mentions via ApeWisdom...")
    apewisdom = fetch_apewisdom()
    if not apewisdom:
        print("\n❌ ApeWisdom returned no data - cannot continue")
        sys.exit(1)
    print(f"   ✓ Got {len(apewisdom)} tickers")
    print("\n📈 Top 15 tickers by Reddit mentions:")
    print("-" * 50)
    for t in apewisdom[:15]:
        change = t["mentions"] - t["mentions_24h_ago"]
        print(f"{t['rank']:3d}. ${t['ticker']:6s} {t['mentions']:5d} mentions "
              f"({'+' if change >= 0 else ''}{change} vs prev 24h)")

    print("\n[STEP 2] Fetching Stocktwits trending + messages...")
    st_trending = fetch_stocktwits_trending()
    print(f"   ✓ Trending on Stocktwits: {', '.join(st_trending[:10]) or 'n/a'}")

    # Detail tickers: top ApeWisdom tickers, plus Stocktwits trending overlap
    detail_tickers = [t["ticker"] for t in apewisdom[:DETAIL_TICKERS]]
    for ticker in st_trending:
        if len(detail_tickers) >= DETAIL_TICKERS + 3:
            break
        if ticker not in detail_tickers:
            detail_tickers.append(ticker)

    ticker_messages = {}
    for ticker in detail_tickers:
        messages = fetch_stocktwits_messages(ticker)
        if messages:
            bullish, bearish = sentiment_ratio(messages)
            print(f"   ✓ ${ticker}: {len(messages)} messages "
                  f"({bullish} bullish / {bearish} bearish tags)")
            ticker_messages[ticker] = messages
        time.sleep(1)

    total_messages = sum(len(m) for m in ticker_messages.values())
    if total_messages == 0:
        print("\n❌ No Stocktwits messages collected - the source is likely")
        print("   blocking this IP. Aborting WITHOUT writing output so the")
        print("   previous good data is not overwritten.")
        sys.exit(1)

    print("\n[STEP 3] Fetching Yahoo Finance trending + per-ticker news...")
    yahoo_trending = fetch_yahoo_trending()
    print(f"   ✓ Trending on Yahoo: {', '.join(yahoo_trending[:10]) or 'n/a'}")

    news_by_ticker = {}
    for ticker in ticker_messages:
        news = fetch_yahoo_news(ticker)
        if news:
            news_by_ticker[ticker] = news
        time.sleep(0.5)
    print(f"   ✓ News headlines for {len(news_by_ticker)} tickers")

    print("\n[STEP 4] Running AI analysis...")
    ai_analysis = get_ai_analysis(apewisdom, ticker_messages, yahoo_trending)

    print("\n[STEP 4b] Deep analysis: community info gaps vs mainstream news...")
    insights = get_overlooked_insights(apewisdom, ticker_messages, news_by_ticker)

    print("\n[STEP 4c] Generating per-ticker details...")
    ticker_details = get_ticker_details(apewisdom, ticker_messages)

    print("\n[STEP 5] Building dashboard data...")
    dashboard_data = build_dashboard_data(
        apewisdom, ticker_messages, yahoo_trending, ai_analysis, ticker_details,
        insights,
    )

    dashboard_dir = os.path.join(project_root, "dashboard", "public", "data")
    if os.path.isdir(dashboard_dir):
        output_path = os.path.join(dashboard_dir, "dashboard_data.json")
    else:
        output_path = os.path.join(current_dir, "dashboard_data.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"💾 Saved: {output_path}")

    print("\n" + "=" * 70)
    print("✅ Scraping complete!")
    print("=" * 70)
