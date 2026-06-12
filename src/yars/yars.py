from __future__ import annotations

import logging
import os
import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .sessions import RandomUserAgentSession

logger = logging.getLogger(__name__)

SUBREDDIT_CATEGORIES = ("hot", "top", "new")
USER_CATEGORIES = ("userhot", "usertop", "usernew")
TIME_FILTERS = ("hour", "day", "week", "month", "year", "all")

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
DEFAULT_OAUTH_USER_AGENT = "yars/0.1 (Reddit data scraper)"


class YARS:
    """Reddit scraper.

    Works in two modes:
    - Anonymous: hits the public www.reddit.com/*.json endpoints. No setup,
      but Reddit blocks many IPs (datacenters, some residential ranges).
    - Authenticated: pass client_id/client_secret (or set REDDIT_CLIENT_ID /
      REDDIT_CLIENT_SECRET env vars) from a free "script" app created at
      https://www.reddit.com/prefs/apps. Requests then go to
      oauth.reddit.com, which works from blocked IPs and has a higher
      rate limit.
    """

    __slots__ = (
        "session",
        "proxy",
        "timeout",
        "_auth",
        "_token",
        "_token_expiry",
    )

    def __init__(
        self,
        proxy=None,
        timeout=10,
        random_user_agent=True,
        client_id=None,
        client_secret=None,
        user_agent=None,
    ):
        client_id = client_id or os.environ.get("REDDIT_CLIENT_ID")
        client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
        self._auth = (client_id, client_secret) if client_id and client_secret else None
        self._token = None
        self._token_expiry = 0.0

        if self._auth:
            # Reddit's API rules require a stable, descriptive user agent
            # for authenticated clients - never a rotating browser one.
            self.session = requests.Session()
            self.session.headers["User-Agent"] = user_agent or DEFAULT_OAUTH_USER_AGENT
        elif random_user_agent:
            self.session = RandomUserAgentSession()
        else:
            self.session = requests.Session()

        self.proxy = proxy
        self.timeout = timeout

        retries = Retry(
            total=5,
            backoff_factor=2,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})

    def _ensure_token(self):
        """Fetch or refresh the OAuth app-only token."""
        if self._token and time.time() < self._token_expiry - 60:
            return
        try:
            response = self.session.post(
                TOKEN_URL,
                auth=self._auth,
                data={"grant_type": "client_credentials"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            token_data = response.json()
            self._token = token_data["access_token"]
        except (requests.RequestException, KeyError, ValueError) as e:
            raise RuntimeError(
                "Reddit OAuth token request failed - check REDDIT_CLIENT_ID / "
                f"REDDIT_CLIENT_SECRET: {e}"
            ) from e
        self._token_expiry = time.time() + token_data.get("expires_in", 3600)
        self.session.headers["Authorization"] = f"bearer {self._token}"
        logger.info("Obtained Reddit OAuth token")

    def _url(self, path):
        """Build the full URL for a Reddit API path like '/r/python/hot'."""
        if self._auth:
            return f"https://oauth.reddit.com{path}"
        return f"https://www.reddit.com{path}.json"

    def _get_json(self, path, params=None):
        """Fetch a Reddit API path and return parsed JSON, or None on failure."""
        if self._auth:
            self._ensure_token()
        url = self._url(path)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Request to %s failed: %s", url, e)
            return None
        try:
            return response.json()
        except ValueError as e:
            logger.warning("Invalid JSON from %s: %s", url, e)
            return None

    def handle_search(self, path, params, after=None, before=None):
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        data = self._get_json(path, params)
        if data is None:
            return []

        results = []
        for post in data.get("data", {}).get("children", []):
            post_data = post["data"]
            results.append(
                {
                    "title": post_data["title"],
                    "link": f"https://www.reddit.com{post_data['permalink']}",
                    "description": post_data.get("selftext", "")[:269],
                }
            )
        logger.info("Search returned %d results", len(results))
        return results

    def search_reddit(self, query, limit=10, after=None, before=None, sort="relevance"):
        params = {"q": query, "limit": limit, "sort": sort, "type": "link"}
        return self.handle_search("/search", params, after, before)

    def search_subreddit(
        self, subreddit, query, limit=10, after=None, before=None, sort="relevance"
    ):
        params = {
            "q": query,
            "limit": limit,
            "sort": sort,
            "type": "link",
            "restrict_sr": "on",
        }
        return self.handle_search(f"/r/{subreddit}/search", params, after, before)

    def scrape_post_details(self, permalink):
        path = permalink.rstrip("/")
        post_data = self._get_json(path)
        if post_data is None:
            return None

        if not isinstance(post_data, list) or len(post_data) < 2:
            logger.warning("Unexpected post data structure for %s", path)
            return None

        main_post = post_data[0]["data"]["children"][0]["data"]
        title = main_post["title"]
        body = main_post.get("selftext", "")

        comments = self._extract_comments(post_data[1]["data"]["children"])
        logger.info("Successfully scraped post: %s", title)
        return {"title": title, "body": body, "comments": comments}

    def _extract_comments(self, comments):
        extracted_comments = []
        for comment in comments:
            if isinstance(comment, dict) and comment.get("kind") == "t1":
                comment_data = comment.get("data", {})
                extracted_comment = {
                    "author": comment_data.get("author", ""),
                    "body": comment_data.get("body", ""),
                    "score": comment_data.get("score", 0),
                    "replies": [],
                }

                replies = comment_data.get("replies", "")
                if isinstance(replies, dict):
                    extracted_comment["replies"] = self._extract_comments(
                        replies.get("data", {}).get("children", [])
                    )
                extracted_comments.append(extracted_comment)
        return extracted_comments

    def scrape_user_data(self, username, limit=10):
        logger.info("Scraping user data for %s, limit: %d", username, limit)
        path = f"/user/{username}/overview"
        after = None
        all_items = []

        while len(all_items) < limit:
            params = {"limit": min(100, limit - len(all_items)), "after": after}
            data = self._get_json(path, params)
            if data is None:
                break

            if "data" not in data or "children" not in data["data"]:
                logger.warning("Unexpected response shape for user %s", username)
                break

            items = data["data"]["children"]
            if not items:
                break

            for item in items:
                kind = item["kind"]
                item_data = item["data"]
                item_url = f"https://www.reddit.com{item_data.get('permalink', '')}"
                if kind == "t3":
                    all_items.append(
                        {
                            "type": "post",
                            "title": item_data.get("title", ""),
                            "subreddit": item_data.get("subreddit", ""),
                            "url": item_url,
                            "created_utc": item_data.get("created_utc", ""),
                        }
                    )
                elif kind == "t1":
                    all_items.append(
                        {
                            "type": "comment",
                            "subreddit": item_data.get("subreddit", ""),
                            "body": item_data.get("body", ""),
                            "created_utc": item_data.get("created_utc", ""),
                            "url": item_url,
                        }
                    )
                if len(all_items) >= limit:
                    break

            after = data["data"].get("after")
            if not after:
                break

            time.sleep(random.uniform(1, 2))

        logger.info("Scraped %d items for user %s", len(all_items), username)
        return all_items

    def fetch_subreddit_posts(
        self, subreddit, limit=10, category="hot", time_filter="all"
    ):
        logger.info(
            "Fetching subreddit/user posts for %s, limit: %d, category: %s, time_filter: %s",
            subreddit,
            limit,
            category,
            time_filter,
        )
        if category not in SUBREDDIT_CATEGORIES + USER_CATEGORIES:
            raise ValueError(
                f"Category must be one of {SUBREDDIT_CATEGORIES} for a subreddit "
                f"or {USER_CATEGORIES} for a user"
            )
        if time_filter not in TIME_FILTERS:
            raise ValueError(f"time_filter must be one of {TIME_FILTERS}")

        if category in USER_CATEGORIES:
            path = f"/user/{subreddit}/submitted"
            params_extra = {"sort": category[4:]}
        else:
            path = f"/r/{subreddit}/{category}"
            params_extra = {}

        after = None
        all_posts = []

        while len(all_posts) < limit:
            params = {
                "limit": min(100, limit - len(all_posts)),
                "after": after,
                "raw_json": 1,
                "t": time_filter,
                **params_extra,
            }
            data = self._get_json(path, params)
            if data is None:
                break

            posts = data.get("data", {}).get("children", [])
            if not posts:
                break

            for post in posts:
                post_data = post["data"]
                post_info = {
                    "title": post_data["title"],
                    "author": post_data["author"],
                    "permalink": post_data["permalink"],
                    "score": post_data["score"],
                    "num_comments": post_data["num_comments"],
                    "created_utc": post_data["created_utc"],
                    "body": post_data.get("selftext", ""),
                }
                if post_data.get("post_hint") == "image" and "url" in post_data:
                    post_info["image_url"] = post_data["url"]
                elif "preview" in post_data and "images" in post_data["preview"]:
                    post_info["image_url"] = post_data["preview"]["images"][0][
                        "source"
                    ]["url"]
                thumbnail = post_data.get("thumbnail") or ""
                # Reddit uses placeholders like "self", "default", "nsfw", "spoiler"
                if thumbnail.startswith("http"):
                    post_info["thumbnail_url"] = thumbnail

                all_posts.append(post_info)
                if len(all_posts) >= limit:
                    break

            after = data["data"].get("after")
            if not after:
                break

            time.sleep(random.uniform(1, 2))

        logger.info("Fetched %d posts for %s", len(all_posts), subreddit)
        return all_posts
