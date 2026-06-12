from __future__ import annotations

import logging
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


class YARS:
    __slots__ = ("session", "proxy", "timeout")

    def __init__(self, proxy=None, timeout=10, random_user_agent=True):
        self.session = (
            RandomUserAgentSession() if random_user_agent else requests.Session()
        )
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

    def _get_json(self, url, params=None):
        """Fetch a URL and return parsed JSON, or None on any failure."""
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

    def handle_search(self, url, params, after=None, before=None):
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        data = self._get_json(url, params)
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
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": limit, "sort": sort, "type": "link"}
        return self.handle_search(url, params, after, before)

    def search_subreddit(
        self, subreddit, query, limit=10, after=None, before=None, sort="relevance"
    ):
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "limit": limit,
            "sort": sort,
            "type": "link",
            "restrict_sr": "on",
        }
        return self.handle_search(url, params, after, before)

    def scrape_post_details(self, permalink):
        url = f"https://www.reddit.com{permalink}.json"
        post_data = self._get_json(url)
        if post_data is None:
            return None

        if not isinstance(post_data, list) or len(post_data) < 2:
            logger.warning("Unexpected post data structure for %s", url)
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
        base_url = f"https://www.reddit.com/user/{username}/.json"
        after = None
        all_items = []

        while len(all_items) < limit:
            params = {"limit": min(100, limit - len(all_items)), "after": after}
            data = self._get_json(base_url, params)
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
            url = f"https://www.reddit.com/user/{subreddit}/submitted/{category[4:]}.json"
        else:
            url = f"https://www.reddit.com/r/{subreddit}/{category}.json"

        after = None
        all_posts = []

        while len(all_posts) < limit:
            params = {
                "limit": min(100, limit - len(all_posts)),
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }
            data = self._get_json(url, params)
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
