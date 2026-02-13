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
    """Extract stock tickers like $TSLA, $AAPL"""
    if not text:
        return []
    tickers = re.findall(r'\$([A-Z]{1,5})\b', str(text))
    # Filter common false positives
    blacklist = {'USD', 'CAD', 'EUR', 'GBP', 'AUD', 'JPY', 'CNY', 'THE', 'ALL', 'FOR', 'ARE', 'NOT', 'BUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'DID', 'GET', 'HIM', 'LET', 'SAY', 'SHE', 'TOO', 'USE'}
    return list(set(t for t in tickers if t not in blacklist))

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

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    top_tickers = dict(ticker_counts.head(20)) if len(ticker_counts) > 0 else {}
    top_posts = posts_df.nlargest(10, 'score')[['title', 'subreddit', 'score', 'num_comments']].to_dict('records')

    subreddit_summary = {}
    for sub in subreddits:
        sub_posts = posts_df[posts_df['subreddit'] == sub]
        if len(sub_posts) > 0:
            subreddit_summary[sub] = {
                'post_count': len(sub_posts),
                'avg_score': round(sub_posts['score'].mean(), 1),
                'top_titles': sub_posts.nlargest(3, 'score')['title'].tolist()
            }

    prompt = f"""Analyze this Reddit finance data snapshot and provide investment insights.

Top ticker mentions (ticker: count): {json.dumps(top_tickers)}

Top posts by score:
{json.dumps(top_posts, indent=2)}

Subreddit breakdown:
{json.dumps(subreddit_summary, indent=2)}

Total posts scraped: {len(posts_df)}
Total comments scraped: {len(comments_df)}

Provide your analysis as JSON with these exact keys:
- "sentiment": object with "overall" (one of "bullish", "bearish", "neutral"), "confidence" (0-100), and "reasoning" (1-2 sentences)
- "themes": array of 4-6 strings describing key narratives/themes
- "tickers_to_watch": array of 3 objects, each with "ticker" (string), "sentiment" ("bullish"/"bearish"/"neutral"), and "reason" (1 sentence)
- "risk_factors": array of 3-4 strings describing risks mentioned
- "contrarian_views": array of 2-3 strings describing notable minority opinions
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

def build_dashboard_data(posts_df, comments_df, ticker_counts, subreddits, ai_analysis):
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

    # Build and save dashboard JSON
    print("\n[STEP 4] Building dashboard data...")
    dashboard_data = build_dashboard_data(posts_df, comments_df, ticker_counts, subreddits, ai_analysis)

    # Save to dashboard/public/data/ if it exists, otherwise save locally
    dashboard_dir = os.path.join(project_root, "dashboard", "public", "data")
    if os.path.isdir(dashboard_dir):
        output_path = os.path.join(dashboard_dir, "dashboard_data.json")
    else:
        output_path = os.path.join(current_dir, "dashboard_data.json")

    with open(output_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"💾 Saved: {output_path}")

    print("\n" + "=" * 70)
    print("✅ Scraping complete!")
    print("=" * 70)
