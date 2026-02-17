#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)

from yars.yars import YARS
import pandas as pd
import re
import time

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-b2a06327ea434feb94b361a1e33f8eb5")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

def extract_tickers(text):
    """Extract stock tickers like $TSLA, AAPL, or well-known company names"""
    if not text:
        return []
    text_str = str(text)

    # Match $TICKER format
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text_str)

    # Match standalone uppercase tickers (2-5 chars, surrounded by spaces/punctuation)
    # Only match known popular tickers to avoid false positives
    known_tickers = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD',
        'NFLX', 'HOOD', 'SNAP', 'BABA', 'NIO', 'PLTR', 'SOFI', 'RIVN', 'LCID',
        'GME', 'AMC', 'BB', 'NOK', 'WISH', 'CLOV', 'SPY', 'QQQ', 'IWM', 'DIA',
        'INTC', 'MU', 'QCOM', 'CRM', 'ORCL', 'UBER', 'LYFT', 'COIN', 'SQ',
        'PYPL', 'V', 'MA', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'SCHW',
        'F', 'GM', 'TM', 'RIVN', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS',
        'JNJ', 'PFE', 'MRNA', 'UNH', 'LLY', 'ABBV', 'BMY', 'MRK',
        'WMT', 'COST', 'TGT', 'HD', 'LOW', 'SBUX', 'MCD', 'NKE',
        'XOM', 'CVX', 'COP', 'BP', 'SHEL', 'BA', 'LMT', 'RTX', 'GE',
        'HIMS', 'CVNA', 'SPOT', 'ROKU', 'RBLX', 'ABNB', 'DKNG',
        'XLE', 'XLF', 'XLK', 'ARKK', 'VTI', 'VOO', 'SCHD',
        'PBR', 'VALE', 'MELI', 'SE', 'GRAB', 'NBIS', 'ASTS',
    }
    bare_tickers = re.findall(r'\b([A-Z]{1,5})\b', text_str)
    bare_matches = [t for t in bare_tickers if t in known_tickers]

    # Filter common false positives
    blacklist = {'USD', 'CAD', 'EUR', 'GBP', 'AUD', 'JPY', 'CNY', 'THE', 'ALL',
                 'FOR', 'ARE', 'NOT', 'BUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY',
                 'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'DID', 'GET', 'HIM',
                 'LET', 'SAY', 'SHE', 'TOO', 'USE', 'FDA', 'CEO', 'IPO', 'ETF',
                 'AI', 'US', 'UK', 'EU', 'GDP', 'CPI', 'FED', 'SEC', 'IRS',
                 'ATH', 'DD', 'YOLO', 'FOMO', 'IMO', 'PSA', 'TIL', 'ELI',
                 'AMA', 'ITM', 'OTM', 'ATM', 'IV', 'PE', 'EPS', 'ER', 'PT',
                 'EDIT', 'RIP', 'FYI', 'BTW', 'LMAO', 'TLDR', 'OG'}

    all_tickers = set(dollar_tickers + bare_matches) - blacklist
    return list(all_tickers)

def scrape_finance():
    miner = YARS()

    subreddits = ['wallstreetbets', 'stocks', 'investing', 'options', 'StockMarket']
    all_posts = []

    for sub in subreddits:
        print(f"\n📊 Scraping r/{sub}...")

        try:
            posts = miner.fetch_subreddit_posts(sub, limit=100, category="hot")
            print(f"   Found {len(posts)} posts")

            for post in posts:
                title = post.get('title', '')
                body = post.get('body', '')
                full_text = f"{title} {body}"

                all_posts.append({
                    'subreddit': sub,
                    'title': title,
                    'body': body,
                    'full_text': full_text,
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc', ''),
                    'author': post.get('author', ''),
                    'permalink': post.get('permalink', ''),
                    'tickers': extract_tickers(full_text)
                })

            print(f"   ✓ Processed {len(posts)} posts")
            time.sleep(3)

        except Exception as e:
            print(f"   ✗ Error: {e}")
            continue

    return pd.DataFrame(all_posts)

def get_comments(df, top_n=100):
    """Get comments from top posts"""
    miner = YARS()
    top_posts = df.nlargest(top_n, 'num_comments')
    all_comments = []

    for idx, post in top_posts.iterrows():
        permalink = post['permalink']
        if not permalink:
            continue

        print(f"\nGetting comments: {post['title'][:50]}...")

        try:
            post_data = miner.scrape_post_details(permalink)
            comments = post_data.get('comments', [])

            for comment in comments:
                comment_text = comment.get('body', '')
                all_comments.append({
                    'post_title': post['title'],
                    'subreddit': post['subreddit'],
                    'comment': comment_text,
                    'score': comment.get('score', 0),
                    'author': comment.get('author', ''),
                    'tickers': extract_tickers(comment_text)
                })

            print(f"   ✓ Got {len(comments)} comments")
            time.sleep(3)

        except Exception as e:
            print(f"   ✗ Error: {e}")

    return pd.DataFrame(all_comments)

def get_ai_analysis(posts_df, ticker_counts, comments_df, subreddits):
    """Use DeepSeek API to analyze scraped data"""
    try:
        from openai import OpenAI
    except ImportError:
        print("   ⚠ openai package not installed. Run: pip install openai")
        return None

    print("\n🤖 Running DeepSeek AI analysis...")

    import httpx
    # Clear proxy env vars that httpx picks up (socks:// not supported)
    env_backup = {}
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        if key in os.environ:
            env_backup[key] = os.environ.pop(key)
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    finally:
        os.environ.update(env_backup)

    top_tickers = {k: int(v) for k, v in ticker_counts.head(20).items()} if len(ticker_counts) > 0 else {}
    top_posts_df = posts_df.nlargest(10, 'score')[['title', 'subreddit', 'score', 'num_comments']]
    top_posts = json.loads(top_posts_df.to_json(orient='records'))

    subreddit_summary = {}
    for sub in subreddits:
        sub_posts = posts_df[posts_df['subreddit'] == sub]
        if len(sub_posts) > 0:
            subreddit_summary[sub] = {
                'post_count': int(len(sub_posts)),
                'avg_score': round(float(sub_posts['score'].mean()), 1),
                'top_titles': sub_posts.nlargest(3, 'score')['title'].tolist()
            }

    prompt = f"""Analyze this Reddit finance data snapshot and provide investment insights. Write in plain, conversational English that a regular investor can understand — no jargon without explanation.

Top ticker mentions (ticker: count): {json.dumps(top_tickers)}

Top posts by score (upvotes):
{json.dumps(top_posts, indent=2)}

Subreddit breakdown:
{json.dumps(subreddit_summary, indent=2)}

Total posts scraped: {len(posts_df)}
Total comments scraped: {len(comments_df)}

Provide your analysis as JSON with these exact keys:

- "sentiment": object with "overall" (one of "bullish", "bearish", "neutral"), "confidence" (0-100), and "reasoning" (2-3 sentences in plain English explaining why the market mood leans this way)

- "themes": array of 4-6 objects, each with "title" (short label, 3-6 words) and "explanation" (2-3 sentences in plain English describing what people are talking about and why it matters for investors)

- "tickers_to_watch": array of 5 objects, each with "ticker" (string), "sentiment" ("bullish"/"bearish"/"neutral"), and "reason" (2-3 sentences in plain English explaining why this stock is worth watching right now, what the Reddit community thinks, and what could move the price). IMPORTANT: Only pick tickers that are actually mentioned in the top ticker list or discussed in the top posts above. Do NOT recommend tickers from your general knowledge that are not present in this Reddit data.

- "risk_factors": array of 3-4 objects, each with "title" (short label) and "explanation" (2-3 sentences in plain English explaining the risk and how it could impact regular investors)

- "contrarian_views": array of 2-3 objects, each with "title" (short label) and "explanation" (2-3 sentences in plain English describing what the minority thinks and why their argument has some merit)

- "sector_breakdown": object mapping sector names to mention counts (e.g. "Technology": 45)

Return ONLY valid JSON, no markdown."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]

        analysis = json.loads(raw)
        print("   ✓ AI analysis complete")
        return analysis

    except Exception as e:
        print(f"   ✗ AI analysis failed: {e}")
        return None

def get_ticker_details(posts_df, comments_df, ticker_counts, ai_analysis=None):
    """Use DeepSeek API to generate per-ticker summaries and sentiment factors"""
    try:
        from openai import OpenAI
    except ImportError:
        print("   ⚠ openai package not installed")
        return {}

    top_tickers = ticker_counts.head(10).index.tolist() if len(ticker_counts) > 0 else []

    # Also include tickers_to_watch from AI analysis so they get details too
    if ai_analysis and 'tickers_to_watch' in ai_analysis:
        for t in ai_analysis['tickers_to_watch']:
            ticker = t.get('ticker', '')
            if ticker and ticker not in top_tickers:
                top_tickers.append(ticker)

    if not top_tickers:
        print("   ⚠ No tickers found, skipping ticker details")
        return {}

    print(f"\n🔍 Generating details for {len(top_tickers)} tickers...")

    # Build per-ticker context from posts and comments
    ticker_context = {}
    for ticker in top_tickers:
        relevant_posts = posts_df[
            posts_df['tickers'].apply(lambda t: ticker in t if isinstance(t, list) else False) |
            posts_df['title'].str.contains(rf'\b{ticker}\b', case=False, na=False)
        ]
        relevant_comments = pd.DataFrame()
        if len(comments_df) > 0:
            relevant_comments = comments_df[
                comments_df['tickers'].apply(lambda t: ticker in t if isinstance(t, list) else False) |
                comments_df['comment'].str.contains(rf'\b{ticker}\b', case=False, na=False)
            ]

        post_samples = []
        for _, row in relevant_posts.head(8).iterrows():
            post_samples.append({
                'title': row['title'],
                'subreddit': row['subreddit'],
                'score': int(row['score']),
                'num_comments': int(row['num_comments']),
            })

        comment_samples = []
        if len(relevant_comments) > 0:
            for _, row in relevant_comments.head(8).iterrows():
                comment_samples.append({
                    'comment': str(row.get('comment', ''))[:300],
                    'subreddit': row.get('subreddit', ''),
                    'score': int(row['score']),
                })

        ticker_context[ticker] = {
            'mention_count': int(ticker_counts.get(ticker, 0)),
            'total_posts': len(relevant_posts),
            'total_comments': len(relevant_comments),
            'posts': post_samples,
            'comments': comment_samples,
        }

    # Clear proxy env vars
    env_backup = {}
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        if key in os.environ:
            env_backup[key] = os.environ.pop(key)
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    finally:
        os.environ.update(env_backup)

    # Process tickers in batches of 2 to avoid token limit issues
    all_details = {}
    batch_size = 2
    for i in range(0, len(top_tickers), batch_size):
        batch = top_tickers[i:i + batch_size]
        batch_context = {t: ticker_context[t] for t in batch}
        print(f"   Processing batch: {', '.join(batch)}...")

        prompt = f"""For each of the following stock tickers, analyze the Reddit community discussion and provide:
1. A ~500-word summary in plain, conversational English about what people are saying, why the stock is getting attention, and what investors should know
2. Exactly 10 positive factors and 10 negative factors being discussed

Here is the Reddit data for each ticker:
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
- For tickers with few Reddit mentions, supplement with general market context about that company
- Write summaries in plain English a regular investor can understand
- Factor descriptions should be concise (5-15 words each)
- Return ONLY valid JSON, no markdown"""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=6000,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0]

            batch_details = json.loads(raw)

            # Attach mention_count from actual data
            for ticker in batch:
                if ticker in batch_details:
                    batch_details[ticker]["mention_count"] = int(ticker_counts.get(ticker, 0))

            all_details.update(batch_details)
            print(f"   ✓ Got details for: {', '.join(batch_details.keys())}")

        except Exception as e:
            print(f"   ✗ Batch failed ({', '.join(batch)}): {e}")

        time.sleep(1)

    print(f"   ✓ Ticker details generated for {len(all_details)} tickers total")
    return all_details


def build_dashboard_data(posts_df, comments_df, ticker_counts, subreddits, ai_analysis, ticker_details=None):
    """Build the consolidated JSON for the dashboard"""
    # Per-subreddit stats
    subreddit_stats = {}
    for sub in subreddits:
        sub_posts = posts_df[posts_df['subreddit'] == sub]
        if len(sub_posts) > 0:
            subreddit_stats[sub] = {
                'post_count': int(len(sub_posts)),
                'avg_score': round(float(sub_posts['score'].mean()), 1),
                'avg_comments': round(float(sub_posts['num_comments'].mean()), 1),
                'total_score': int(sub_posts['score'].sum()),
            }

    # Per-subreddit ticker breakdown
    subreddit_tickers = {}
    for sub in subreddits:
        sub_posts = posts_df[posts_df['subreddit'] == sub]
        sub_tickers = []
        for tickers in sub_posts['tickers']:
            if isinstance(tickers, list):
                sub_tickers.extend(tickers)
        if sub_tickers:
            subreddit_tickers[sub] = dict(pd.Series(sub_tickers).value_counts().head(20))

    # Convert posts and comments to plain dicts (drop full_text to save space)
    posts_list = []
    for _, row in posts_df.iterrows():
        posts_list.append({
            'subreddit': row['subreddit'],
            'title': row['title'],
            'body': str(row.get('body', ''))[:500],
            'score': int(row['score']),
            'num_comments': int(row['num_comments']),
            'created_utc': float(row['created_utc']) if row['created_utc'] else 0,
            'author': row['author'],
            'permalink': row['permalink'],
            'tickers': row['tickers'] if isinstance(row['tickers'], list) else [],
        })

    comments_list = []
    if len(comments_df) > 0:
        for _, row in comments_df.iterrows():
            comments_list.append({
                'post_title': row['post_title'],
                'subreddit': row.get('subreddit', ''),
                'comment': str(row.get('comment', ''))[:500],
                'score': int(row['score']),
                'author': row['author'],
                'tickers': row['tickers'] if isinstance(row['tickers'], list) else [],
            })

    # Global ticker mentions as dict
    ticker_dict = dict(zip(
        ticker_counts.index.tolist(),
        [int(x) for x in ticker_counts.values.tolist()]
    )) if len(ticker_counts) > 0 else {}

    # Fallback AI analysis
    if ai_analysis is None:
        ai_analysis = {
            "sentiment": {"overall": "neutral", "confidence": 0, "reasoning": "AI analysis unavailable"},
            "themes": [],
            "tickers_to_watch": [],
            "risk_factors": [],
            "contrarian_views": [],
            "sector_breakdown": {},
        }

    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "subreddits": subreddits,
        "posts": posts_list,
        "comments": comments_list,
        "ticker_mentions": ticker_dict,
        "subreddit_tickers": subreddit_tickers,
        "subreddit_stats": subreddit_stats,
        "ai_analysis": ai_analysis,
        "ticker_details": ticker_details or {},
    }


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Reddit Finance Scraper")
    print("=" * 70)

    subreddits = ['wallstreetbets', 'stocks', 'investing', 'options', 'StockMarket']

    # Scrape posts
    print("\n[STEP 1] Scraping finance subreddits...")
    posts_df = scrape_finance()

    if len(posts_df) == 0:
        print("\n❌ No posts scraped")
        exit()

    print(f"\n✅ Total posts: {len(posts_df)}")

    # Save posts CSV
    posts_df.to_csv('reddit_finance_posts.csv', index=False)
    print(f"💾 Saved: reddit_finance_posts.csv")

    # Ticker analysis
    all_tickers = []
    for tickers in posts_df['tickers']:
        if isinstance(tickers, list):
            all_tickers.extend(tickers)

    ticker_counts = pd.Series(all_tickers).value_counts() if all_tickers else pd.Series(dtype=int)

    if len(ticker_counts) > 0:
        print("\n📈 Top 15 Tickers Mentioned:")
        print("-" * 40)
        for i, (ticker, count) in enumerate(ticker_counts.head(15).items(), 1):
            print(f"{i:2d}. ${ticker:5s} - {count:3d} mentions")

        ticker_df = pd.DataFrame({
            'ticker': ticker_counts.index,
            'mentions': ticker_counts.values
        })
        ticker_df.to_csv('ticker_mentions.csv', index=False)
        print(f"\n💾 Saved: ticker_mentions.csv")

    # Get comments
    print("\n[STEP 2] Getting comments from top 100 posts...")
    comments_df = get_comments(posts_df, top_n=100)

    if len(comments_df) > 0:
        comments_df.to_csv('reddit_comments.csv', index=False)
        print(f"\n✅ Comments scraped: {len(comments_df)}")
        print(f"💾 Saved: reddit_comments.csv")

    # AI Analysis
    print("\n[STEP 3] Running AI analysis...")
    ai_analysis = get_ai_analysis(posts_df, ticker_counts, comments_df, subreddits)

    # Per-ticker details
    print("\n[STEP 3b] Generating per-ticker details...")
    ticker_details = get_ticker_details(posts_df, comments_df, ticker_counts, ai_analysis)

    # Build and save dashboard JSON
    print("\n[STEP 4] Building dashboard data...")
    dashboard_data = build_dashboard_data(posts_df, comments_df, ticker_counts, subreddits, ai_analysis, ticker_details)

    # Save to dashboard/public/data/ if it exists, otherwise save locally
    dashboard_dir = os.path.join(project_root, "dashboard", "public", "data")
    if os.path.isdir(dashboard_dir):
        output_path = os.path.join(dashboard_dir, "dashboard_data.json")
    else:
        output_path = os.path.join(current_dir, "dashboard_data.json")

    import numpy as np
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(output_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2, cls=NumpyEncoder)
    print(f"💾 Saved: {output_path}")

    print("\n" + "=" * 70)
    print("✅ Scraping complete!")
    print("=" * 70)
